import re
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Message
from nonebot.log import logger

from ..core.models import AuthPacket, ChatPacket, EventPacket, CommandResponsePacket
from ..core.connection import Session, manager


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
        clean_message = self._clean_text(packet.message)
        if packet.user_name in ["RCON", "Server", "System"]:
            msg = clean_message
        else:
            msg = f"<{packet.user_name}> {clean_message}"
        await self._send_to_group(session.group_id, msg)

    async def _handle_event(self, session: Session, packet: EventPacket):
        prefix = f"[{session.server_name}] "
        msg = ""
        if packet.event_type == "world_load":
            msg = f"🌍 世界已加载: {packet.world_name}\n📝 {packet.motd}"
        elif packet.event_type == "world_unload":
            msg = f"🛑 服务器已停止: {packet.world_name}"

        if msg:
            await self._send_to_group(session.group_id, prefix + msg)

    def _clean_text(self, text: str) -> str:
        pattern = r"\[c\/[\da-fA-F]+:(.+?)\]"
        while re.search(pattern, text):
            text = re.sub(pattern, r"\1", text)
        return text

    async def _send_to_group(self, group_id: int, message: str):
        if not group_id:
            return
        try:
            bot = get_bot()
            await bot.send_group_msg(group_id=group_id, message=Message(message))
        except Exception:
            pass


bridge = BridgeService()
