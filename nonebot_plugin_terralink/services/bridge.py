from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Message
from nonebot.log import logger

from ..core.models import AuthPacket, ChatPacket, EventPacket
from ..core.connection import Session, manager


class BridgeService:
    """
    业务层：处理 TML 发来的数据包，并转发到对应的 QQ 群
    """

    async def handle_incoming_data(self, session: Session, raw_data: dict):
        msg_type = raw_data.get("type")

        # 1. 鉴权优先
        if msg_type == "auth":
            await self._handle_auth(session, raw_data)
            return

        # 2. 拦截未鉴权
        if not session.is_ready:
            # TML 协议规定未鉴权应丢弃包
            return

        # 3. 业务分发
        try:
            if msg_type == "chat":
                await self._handle_chat(session, ChatPacket(**raw_data))
            elif msg_type == "event":
                await self._handle_event(session, EventPacket(**raw_data))
            elif msg_type == "command":
                # command 类型在 S->C 方向通常是回显
                await self._handle_chat(session, ChatPacket(**raw_data))
        except Exception as e:
            logger.error(f"[TerraLink] 业务处理错误: {e}")

    async def _handle_auth(self, session: Session, data: dict):
        try:
            packet = AuthPacket(**data)
            # 委托 Manager 进行 Token 验证和绑定
            if manager.authenticate(session.ws, packet.token):
                await session.send_auth_response(True, "Authentication Successful!")
            else:
                await session.send_auth_response(False, "Invalid Token")
                # 协议: 鉴权失败断开
                await session.ws.close()
        except Exception as e:
            logger.error(f"[TerraLink] 鉴权异常: {e}")

    async def _handle_chat(self, session: Session, packet: ChatPacket):
        """处理聊天转发与指令回显"""
        # RCON (系统/指令回显) 不加前缀，玩家加前缀
        if packet.user_name in ["RCON", "Server", "System"]:
            msg = packet.message
        else:
            msg = f"<{packet.user_name}> {packet.message}"

        await self._send_to_group(session.group_id, msg)

    async def _handle_event(self, session: Session, packet: EventPacket):
        """处理事件广播"""
        # 可选：加上服务器名前缀，方便群内区分
        prefix = f"[{session.server_name}] "

        msg = ""
        if packet.event_type == "world_load":
            msg = f"🌍 世界已加载: {packet.world_name}\n📝 {packet.motd}"
        elif packet.event_type == "world_unload":
            msg = f"🛑 服务器已停止: {packet.world_name}"
        elif packet.event_type == "boss_spawn":
            msg = f"💀 {packet.motd}"
        elif packet.event_type == "boss_kill":
            msg = f"🎉 {packet.motd}"
        # server_ready 通常不广播，仅作为心跳起点

        if msg:
            await self._send_to_group(session.group_id, prefix + msg)

    async def _send_to_group(self, group_id: int, message: str):
        if not group_id:
            return
        try:
            bot = get_bot()
            await bot.send_group_msg(group_id=group_id, message=Message(message))
        except Exception as e:
            # 这里的异常通常是因为 Bot 未连接，忽略即可
            pass


bridge = BridgeService()
