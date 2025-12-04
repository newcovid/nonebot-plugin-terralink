from pydantic import BaseModel
from typing import Optional, List, Literal, Any
import time

# --- 基础协议包 ---


class BasePacket(BaseModel):
    """所有数据包的基类"""

    type: str
    timestamp: int = int(time.time())


# --- 接收 (TML -> Nonebot) ---


class AuthPacket(BasePacket):
    """鉴权请求包"""

    type: Literal["auth"]
    token: str


class ChatPacket(BasePacket):
    """
    聊天消息包 / 指令回显包
    文档 5.1: 包含游戏内玩家聊天，以及指令执行的结果回显
    """

    type: Literal["chat"]
    user_name: str
    message: str
    color: Optional[str] = None


class EventPacket(BasePacket):
    """
    系统事件包
    文档 5.2: 服务器状态变更或游戏内重要事件
    """

    type: Literal["event"]
    event_type: str
    world_name: str
    motd: Optional[str] = None


# --- 发送 (Nonebot -> TML) ---


class AuthResponsePacket(BaseModel):
    """鉴权响应包"""

    type: Literal["auth_response"] = "auth_response"
    success: bool
    message: str
    timestamp: int = int(time.time())


class CommandPacket(BaseModel):
    """
    执行指令包
    文档 4.2: 远程执行模组提供的管理指令
    """

    type: Literal["command"] = "command"
    command: str
    args: List[str] = []
    timestamp: int = int(time.time())


class ServerChatPacket(BaseModel):
    """
    发送聊天消息包
    文档 4.1: 将 QQ 群消息转发到游戏内
    """

    type: Literal["chat"] = "chat"
    user_name: str
    message: str
    color: Optional[str] = None
    timestamp: int = int(time.time())
