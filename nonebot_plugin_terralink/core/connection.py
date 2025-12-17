import json
import asyncio
import uuid
from typing import Optional, Any, Dict
from nonebot import get_plugin_config
from nonebot.log import logger
import websockets

from ..config import Config, LinkConfig
from .models import (
    AuthResponsePacket,
    CommandPacket,
    ServerChatPacket,
    CommandResponsePacket,
)

plugin_config = get_plugin_config(Config)


class Session:
    """
    代表一个 TML 服务器连接实例
    [Update] 实现了基于 UUID 的全双工异步指令匹配
    """

    def __init__(self, ws: Any, remote_addr: str):
        self.ws = ws
        self.remote_addr = remote_addr
        self.config: Optional[LinkConfig] = None
        self._authenticated: bool = False

        # [Update] 从 Deque 改为 Dict
        # Key: RequestID (UUID str)
        # Value: asyncio.Future (等待结果的锚点)
        self._pending_commands: Dict[str, asyncio.Future] = {}

    @property
    def is_ready(self) -> bool:
        return self._authenticated and self.config is not None

    @property
    def group_id(self) -> int:
        return self.config.group_id if self.config else 0

    @property
    def server_name(self) -> str:
        return self.config.name if self.config else self.remote_addr

    async def send_json(self, data: dict) -> bool:
        """核心发送逻辑"""
        if self.ws is None:
            return False
        try:
            json_str = json.dumps(data)
            await self.ws.send(json_str)
            if data.get("type") != "auth_response":
                logger.debug(f"[TerraLink] Sent -> {self.server_name}: {json_str}")
            return True
        except Exception as e:
            logger.error(f"[TerraLink] Send Error ({self.server_name}): {e}")
            return False

    async def send_auth_response(self, success: bool, message: str):
        packet = AuthResponsePacket(success=success, message=message)
        # [Fix] Pydantic v2: use model_dump() instead of dict()
        await self.send_json(packet.model_dump())

    async def send_chat(self, user: str, msg: str) -> bool:
        if not self.is_ready:
            return False
        packet = ServerChatPacket(user_name=user, message=msg)
        # [Fix] Pydantic v2: use model_dump() instead of dict()
        return await self.send_json(packet.model_dump())

    async def execute_command(
        self, command: str, args: list = None, timeout: float = 10.0
    ) -> CommandResponsePacket:
        """
        发送指令并等待结果 (ID 匹配模式)
        """
        if not self.is_ready:
            raise RuntimeError("Session not ready")

        # 1. 生成唯一 ID
        req_id = str(uuid.uuid4())

        # 2. 创建 Future 并存入字典
        future = asyncio.get_running_loop().create_future()
        self._pending_commands[req_id] = future

        try:
            # 3. 发送带 ID 的数据包
            packet = CommandPacket(command=command, args=args or [], id=req_id)
            # [Fix] Pydantic v2: use model_dump() instead of dict()
            success = await self.send_json(packet.model_dump())

            if not success:
                raise RuntimeError("Failed to send command packet")

            # 4. 等待特定 ID 的结果
            return await asyncio.wait_for(future, timeout)

        except Exception:
            raise
        finally:
            # 5. 清理字典 (无论成功、失败还是超时，都必须移除，防止内存泄漏)
            self._pending_commands.pop(req_id, None)

    def handle_command_response(self, packet: CommandResponsePacket):
        """
        处理收到的指令响应
        通过 packet.id 精准找到对应的 Future
        """
        if not packet.id:
            # 如果是旧版模组或异常包没有 ID，记录日志并忽略
            logger.warning(
                f"[TerraLink] Received response without ID: {packet.message}"
            )
            return

        future = self._pending_commands.get(packet.id)
        if future:
            if not future.done():
                future.set_result(packet)
        else:
            # 可能是超时后才收到的包，或者 ID 错误
            logger.debug(f"[TerraLink] Received orphaned response for ID: {packet.id}")


class SessionManager:
    """管理所有 TML 连接的容器"""

    def __init__(self):
        self._sessions_by_ws: Dict[Any, Session] = {}
        self._sessions_by_group: Dict[int, Session] = {}

    def register(self, ws: Any, remote_addr: str) -> Session:
        session = Session(ws, remote_addr)
        self._sessions_by_ws[ws] = session
        logger.info(f"[TerraLink] New Connection: {remote_addr}")
        return session

    def unregister(self, ws: Any):
        if ws in self._sessions_by_ws:
            session = self._sessions_by_ws.pop(ws)
            if session.config and session.config.group_id in self._sessions_by_group:
                if self._sessions_by_group[session.config.group_id] == session:
                    del self._sessions_by_group[session.config.group_id]

            # 清理所有挂起的任务，通知它们连接断开了
            for req_id, future in session._pending_commands.items():
                if not future.done():
                    future.set_exception(ConnectionError("Connection closed"))

            # 快速清空
            session._pending_commands.clear()

            logger.info(f"[TerraLink] Disconnected: {session.server_name}")

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
            logger.warning(f"[TerraLink] Auth Failed: Token '{token}' not found")
            return False

        session.config = matched_config
        session._authenticated = True
        self._sessions_by_group[matched_config.group_id] = session

        logger.success(
            f"[TerraLink] Auth Success: [{matched_config.name}] <-> [Group {matched_config.group_id}]"
        )
        return True


manager = SessionManager()
