import re
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Message
from nonebot.log import logger

from ..core.models import AuthPacket, ChatPacket, EventPacket, CommandResponsePacket
from ..core.connection import Session, manager
from .group_settings import group_settings

# 模组以这些名称发送系统播报
SYSTEM_SENDERS = {"RCON", "Server", "System"}

# event 包类型对应的播报分类
EVENT_CATEGORIES = {
    "server_ready": "server",
    "world_load": "server",
    "world_unload": "server",
    "boss_spawn": "boss",
    "boss_kill": "boss",
}

# 游戏聊天标签格式: [tag/options:text]，与 tModLoader ChatManager 一致
CHAT_TAG_PATTERN = re.compile(
    r"(?<!\\)\[(?P<tag>[a-zA-Z]{1,10})(?:/(?P<options>[^:\]]+))?:(?P<text>.+?)(?<!\\)\]"
)


class BridgeService:
    """
    业务层：处理 TML 发来的数据包
    """

    async def handle_incoming_data(self, session: Session, raw_data: dict):
        msg_type = raw_data.get("type")

        # 1. 鉴权优先
        if msg_type == "auth":
            await self._handle_auth(session, raw_data)
            return

        # 2. 拦截未鉴权
        if not session.is_ready:
            return

        try:
            # 3. 业务分发
            if msg_type == "chat":
                await self._handle_chat(session, ChatPacket(**raw_data))

            elif msg_type == "event":
                await self._handle_event(session, EventPacket(**raw_data))

            elif msg_type == "command_response":
                # 解析包 (包含 ID) 并交给 Session 进行路由
                packet = CommandResponsePacket(**raw_data)
                session.handle_command_response(packet)

            else:
                logger.debug(f"[TerraLink] Unknown packet type: {msg_type}")

        except Exception as e:
            logger.error(f"[TerraLink] Business Error: {e}")

    async def _handle_auth(self, session: Session, data: dict):
        try:
            packet = AuthPacket(**data)
            if manager.authenticate(session.ws, packet.token):
                await session.send_auth_response(True, "Authentication Successful!")
            else:
                await session.send_auth_response(False, "Invalid Token")
                await session.ws.close()
        except Exception:
            pass

    async def _handle_chat(self, session: Session, packet: ChatPacket):
        if not group_settings.is_server_to_group_enabled(session.group_id):
            logger.debug(f"[TerraLink] 群 {session.group_id} 的服务器聊天转发已关闭")
            return

        is_system = packet.user_name in SYSTEM_SENDERS
        # 旧版模组不携带 category，只能按发送者区分玩家聊天与系统播报
        category = packet.category or ("system" if is_system else "chat")
        if category != "chat" and not group_settings.is_category_enabled(
            session.group_id, category
        ):
            logger.debug(
                f"[TerraLink] 群 {session.group_id} 已关闭 {category} 类播报，忽略: {packet.message}"
            )
            return

        clean_message = self._clean_text(packet.message)
        if not clean_message.strip():
            return
        if is_system:
            msg = clean_message
        else:
            msg = f"<{packet.user_name}> {clean_message}"
        await self._send_to_group(session.group_id, msg)

    async def _handle_event(self, session: Session, packet: EventPacket):
        category = EVENT_CATEGORIES.get(packet.event_type)
        if not group_settings.is_category_enabled(session.group_id, category):
            logger.debug(
                f"[TerraLink] 群 {session.group_id} 的事件播报已关闭: {packet.event_type}"
            )
            return

        # boss_spawn / boss_kill 不在此处转发：原版的 Boss 苏醒/击败播报
        # 已作为 boss 类 chat 包发送，重复转发会刷屏
        prefix = f"[{session.server_name}] "
        msg = ""
        if packet.event_type == "world_load":
            msg = f"世界已加载: {packet.world_name}\n{packet.motd}"
        elif packet.event_type == "world_unload":
            msg = f"服务器已停止: {packet.world_name}"

        if msg:
            await self._send_to_group(session.group_id, prefix + msg)

    def _clean_text(self, text: str) -> str:
        """
        去除游戏聊天标签。新版模组已在服务端转换为可读文本，
        这里兜底处理旧版模组发来的原始标签 (如 [i/d...:ItemID]、[c/FF0000:文字])
        """
        for _ in range(3):
            cleaned = CHAT_TAG_PATTERN.sub(self._render_tag, text)
            if cleaned == text:
                break
            text = cleaned
        return text

    @staticmethod
    def _render_tag(match: "re.Match[str]") -> str:
        tag = match.group("tag").lower()
        inner = match.group("text")
        if tag in ("c", "color", "n", "name", "a", "achievement"):
            return inner
        if tag in ("i", "item"):
            # 模组物品为 "ModName/ItemName"，原版物品为数字 ID
            name = inner.rsplit("/", 1)[-1]
            return f"[物品#{name}]" if name.isdigit() else f"[{name}]"
        if tag in ("g", "glyph"):
            return ""
        return match.group(0)

    async def _send_to_group(self, group_id: int, message: str):
        if not group_id:
            return
        try:
            bot = get_bot()
            await bot.send_group_msg(group_id=group_id, message=Message(message))
        except Exception as e:
            logger.warning(f"[TerraLink] 转发到群 {group_id} 失败: {e}")


bridge = BridgeService()
