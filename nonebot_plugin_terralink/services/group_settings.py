import json
from pathlib import Path
from typing import Any, Dict, Optional

from nonebot import get_plugin_config
from nonebot.log import logger
from pydantic import BaseModel

from ..config import Config

plugin_config = get_plugin_config(Config)


class GroupSettings(BaseModel):
    event_broadcast: bool = True
    group_to_server: bool = True
    server_to_group: bool = True


class GroupSettingsStore:
    def __init__(self, path: Optional[str] = None):
        self.path = self._resolve_path(path)
        self._settings: Dict[int, GroupSettings] = {}
        self._load()

    def _resolve_path(self, path: Optional[str]) -> Path:
        if path:
            return Path(path).expanduser()
        return Path("data") / "terralink" / "group_settings.json"

    def _load(self):
        if not self.path.exists():
            return

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"[TerraLink] 读取群设置失败，将使用默认设置: {e}")
            return

        if not isinstance(raw, dict):
            logger.warning("[TerraLink] 群设置文件格式无效，将使用默认设置")
            return

        for group_id, settings in raw.items():
            try:
                self._settings[int(group_id)] = GroupSettings(**settings)
            except Exception as e:
                logger.warning(
                    f"[TerraLink] 群 {group_id} 的设置无效，已忽略: {e}"
                )

    def _save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                str(group_id): settings.model_dump()
                for group_id, settings in self._settings.items()
            }
            self.path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"[TerraLink] 保存群设置失败: {e}")

    def get(self, group_id: Any) -> GroupSettings:
        normalized_group_id = self._normalize_group_id(group_id)
        if normalized_group_id is None:
            return GroupSettings()
        return self._settings.get(normalized_group_id, GroupSettings())

    def update(self, group_id: Any, **changes: bool) -> GroupSettings:
        normalized_group_id = self._normalize_group_id(group_id)
        if normalized_group_id is None:
            raise ValueError(f"无效群号: {group_id!r}")

        current = self.get(normalized_group_id)
        data = current.model_dump()
        data.update(changes)
        settings = GroupSettings(**data)
        self._settings[normalized_group_id] = settings
        self._save()
        return settings

    def reset(self, group_id: Any) -> GroupSettings:
        normalized_group_id = self._normalize_group_id(group_id)
        if normalized_group_id is None:
            raise ValueError(f"无效群号: {group_id!r}")

        self._settings.pop(normalized_group_id, None)
        self._save()
        return GroupSettings()

    def is_event_enabled(self, group_id: Any) -> bool:
        return self.get(group_id).event_broadcast

    def is_group_to_server_enabled(self, group_id: Any) -> bool:
        return self.get(group_id).group_to_server

    def is_server_to_group_enabled(self, group_id: Any) -> bool:
        return self.get(group_id).server_to_group

    @staticmethod
    def _normalize_group_id(group_id: Any) -> Optional[int]:
        try:
            return int(group_id)
        except (TypeError, ValueError):
            return None


group_settings = GroupSettingsStore(plugin_config.terralink_state_path)
