import re
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Message
from nonebot.log import logger

from ..core.models import AuthPacket, ChatPacket, EventPacket
from ..core.connection import Session, manager


class BridgeService:
    """
    业务层：处理 TML 发来的数据包，并转发到对应的 QQ 群
    """

    def _clean_text(self, text: str) -> str:
        """
        去除 Terraria 的颜色标签
        示例: DPSExtreme: [c/ffffff:史莱姆王] -> DPSExtreme: 史莱姆王
        """
        # 正则匹配 [c/HexCode:Content]
        # 使用 while 循环以支持可能的嵌套标签
        pattern = r"\[c\/[\da-fA-F]+:(.+?)\]"
        while re.search(pattern, text):
            text = re.sub(pattern, r"\1", text)
        return text

    async def handle_incoming_data(self, session: Session, raw_data: dict):
        msg_type = raw_data.get("type")

        # 1. 鉴权优先
        if msg_type == "auth":
            await self._handle_auth(session, raw_data)
            return

        # 2. 拦截未鉴权
        if not session.is_ready:
            return

        # 3. 业务分发
        try:
            if msg_type == "chat":
                await self._handle_chat(session, ChatPacket(**raw_data))
            elif msg_type == "event":
                await self._handle_event(session, EventPacket(**raw_data))
            elif msg_type == "command":
                await self._handle_chat(session, ChatPacket(**raw_data))
        except Exception as e:
            logger.error(f"[TerraLink] 业务处理错误: {e}")

    async def _handle_auth(self, session: Session, data: dict):
        try:
            packet = AuthPacket(**data)
            if manager.authenticate(session.ws, packet.token):
                await session.send_auth_response(True, "Authentication Successful!")
            else:
                await session.send_auth_response(False, "Invalid Token")
                await session.ws.close()
        except Exception as e:
            logger.error(f"[TerraLink] 鉴权异常: {e}")

    async def _handle_chat(self, session: Session, packet: ChatPacket):
        """处理聊天转发与指令回显"""

        # [优化] 清理消息中的颜色代码
        clean_message = self._clean_text(packet.message)

        # RCON (系统/指令回显) 不加前缀，玩家加前缀
        if packet.user_name in ["RCON", "Server", "System"]:
            msg = clean_message
        else:
            msg = f"<{packet.user_name}> {clean_message}"

        await self._send_to_group(session.group_id, msg)

    async def _handle_event(self, session: Session, packet: EventPacket):
        """处理事件广播"""
        prefix = f"[{session.server_name}] "

        msg = ""
        if packet.event_type == "world_load":
            msg = f"🌍 世界已加载: {packet.world_name}\n📝 {packet.motd}"
        elif packet.event_type == "world_unload":
            msg = f"🛑 服务器已停止: {packet.world_name}"

        # [优化] Boss 事件预留位置，但不发送消息，避免与游戏内广播重复
        elif packet.event_type == "boss_spawn":
            # msg = f"💀 {packet.motd}"
            pass
        elif packet.event_type == "boss_kill":
            # msg = f"🎉 {packet.motd}"
            pass

        if msg:
            await self._send_to_group(session.group_id, prefix + msg)

    async def _send_to_group(self, group_id: int, message: str):
        if not group_id:
            return
        try:
            bot = get_bot()
            await bot.send_group_msg(group_id=group_id, message=Message(message))
        except Exception as e:
            pass


bridge = BridgeService()
