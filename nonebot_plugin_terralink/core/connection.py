import json
import asyncio
from typing import Optional, Any, Dict
from nonebot import get_plugin_config
from nonebot.log import logger
import websockets

from ..config import Config, LinkConfig
from .models import AuthResponsePacket, CommandPacket, ServerChatPacket

plugin_config = get_plugin_config(Config)


class Session:
    """
    代表一个 TML 服务器连接实例
    """

    def __init__(self, ws: Any, remote_addr: str):
        self.ws = ws
        self.remote_addr = remote_addr
        self.config: Optional[LinkConfig] = None
        self._authenticated: bool = False

    @property
    def is_ready(self) -> bool:
        """会话是否已就绪（已连接 + 已鉴权 + 已绑定配置）"""
        # 这里只做逻辑层面的检查，物理连接状态由 send 时的异常处理负责
        return self._authenticated and self.config is not None

    @property
    def group_id(self) -> int:
        return self.config.group_id if self.config else 0

    @property
    def server_name(self) -> str:
        return self.config.name if self.config else self.remote_addr

    async def send_json(self, data: dict) -> bool:
        """
        核心发送逻辑：直接发送，捕获异常
        """
        if self.ws is None:
            logger.warning(
                f"[TerraLink] 发送失败: Session 未关联 WebSocket ({self.server_name})"
            )
            return False

        try:
            json_str = json.dumps(data)
            await self.ws.send(json_str)

            # 调试日志：不打印鉴权包，避免刷屏，其他包打印内容
            if data.get("type") != "auth_response":
                logger.debug(f"[TerraLink] Sent to {self.server_name}: {json_str}")
            return True

        except websockets.exceptions.ConnectionClosed as e:
            # 捕获所有连接关闭异常 (包含 OK 和 Error)
            logger.warning(
                f"[TerraLink] 发送失败: 连接已断开 ({self.server_name}) | Code: {e.code}, Reason: {e.reason}"
            )
            # 可以在这里主动触发清理逻辑，虽然 server.py 也会处理
            return False
        except Exception as e:
            # 捕获其他未预料的异常
            logger.error(
                f"[TerraLink] 发送异常 ({self.server_name}): {type(e).__name__} - {e}"
            )
            return False

    async def send_auth_response(self, success: bool, message: str):
        packet = AuthResponsePacket(success=success, message=message)
        await self.send_json(packet.dict())

    async def send_command(self, command: str, args: list = None) -> bool:
        if not self.is_ready:
            return False
        packet = CommandPacket(command=command, args=args or [])
        return await self.send_json(packet.dict())

    async def send_chat(self, user: str, msg: str) -> bool:
        if not self.is_ready:
            return False
        packet = ServerChatPacket(user_name=user, message=msg)
        return await self.send_json(packet.dict())


class SessionManager:
    """
    管理所有 TML 连接的容器
    """

    def __init__(self):
        self._sessions_by_ws: Dict[Any, Session] = {}
        self._sessions_by_group: Dict[int, Session] = {}

    def register(self, ws: Any, remote_addr: str) -> Session:
        session = Session(ws, remote_addr)
        self._sessions_by_ws[ws] = session
        logger.info(f"[TerraLink] 新连接接入: {remote_addr} (等待鉴权)")
        return session

    def unregister(self, ws: Any):
        if ws in self._sessions_by_ws:
            session = self._sessions_by_ws.pop(ws)
            # 只有当映射确实是该 Session 时才移除
            if session.config and session.config.group_id in self._sessions_by_group:
                if self._sessions_by_group[session.config.group_id] == session:
                    del self._sessions_by_group[session.config.group_id]
            logger.info(f"[TerraLink] 连接清理完成: {session.server_name}")

    def get_session_by_group(self, group_id: int) -> Optional[Session]:
        return self._sessions_by_group.get(group_id)

    def authenticate(self, ws: Any, token: str) -> bool:
        session = self._sessions_by_ws.get(ws)
        if not session:
            return False

        matched_config = next(
            (c for c in plugin_config.terralink_links if c.token == token), None
        )

        if not matched_config:
            logger.warning(f"[TerraLink] 鉴权失败: Token '{token}' 未在配置中找到")
            return False

        # 检查顶号
        if matched_config.group_id in self._sessions_by_group:
            old_session = self._sessions_by_group[matched_config.group_id]
            if (
                old_session != session
            ):  # 这里不需要判断 old_session.is_connected，直接覆盖映射即可
                logger.warning(
                    f"[TerraLink] 群 {matched_config.group_id} 的连接映射已更新 (旧连接被顶替)"
                )

        session.config = matched_config
        session._authenticated = True
        self._sessions_by_group[matched_config.group_id] = session

        logger.success(
            f"[TerraLink] 鉴权成功: [{matched_config.name}] <-> [群 {matched_config.group_id}]"
        )
        return True


# 全局单例
manager = SessionManager()
