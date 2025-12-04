import asyncio
import json
import websockets
from websockets.exceptions import (
    ConnectionClosed,
    ConnectionClosedError,
    ConnectionClosedOK,
)
from nonebot import get_driver, get_plugin_config
from nonebot.log import logger

from ..config import Config
from .connection import manager
from ..services.bridge import bridge

driver = get_driver()
plugin_config = get_plugin_config(Config)
server_task = None


async def ws_handler(websocket):
    """WebSocket 连接处理循环"""
    remote_addr = str(getattr(websocket, "remote_address", "Unknown"))

    # 1. 注册物理连接
    session = manager.register(websocket, remote_addr)

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                # 2. 将数据包 + 会话上下文 交给业务层
                await bridge.handle_incoming_data(session, data)
            except json.JSONDecodeError:
                logger.warning(f"[TerraLink] 忽略非 JSON 数据: {message}")
            except Exception as e:
                logger.error(f"[TerraLink] 数据包处理业务逻辑异常: {e}")

    except ConnectionClosedOK:
        logger.info(f"[TerraLink] 客户端正常断开连接: {remote_addr}")
    except ConnectionClosedError as e:
        logger.warning(
            f"[TerraLink] 客户端异常断开: {remote_addr} | Code: {e.code}, Reason: {e.reason}"
        )
    except Exception as e:
        logger.error(f"[TerraLink] WebSocket 底层异常: {type(e).__name__} - {e}")
    finally:
        # 3. 清理连接
        manager.unregister(websocket)


async def start_server():
    host = "0.0.0.0"
    port = plugin_config.terralink_port

    logger.info(f"[TerraLink] WebSocket 服务启动中，监听端口: {port}")
    try:
        # [关键设置] ping_interval=None: 禁用服务器端 Ping
        # 这对于 TModLoader 这种可能不响应 Ping 的客户端至关重要
        async with websockets.serve(ws_handler, host, port, ping_interval=None):
            logger.success(f"[TerraLink] 服务启动成功，等待 TML 连接...")
            await asyncio.Future()  # 永久挂起
    except asyncio.CancelledError:
        logger.info("[TerraLink] 服务正在停止...")
    except OSError as e:
        logger.error(f"[TerraLink] 端口 {port} 被占用或无法绑定: {e}")


@driver.on_startup
async def _():
    global server_task
    if plugin_config.terralink_enabled:
        server_task = asyncio.create_task(start_server())


@driver.on_shutdown
async def _():
    if server_task:
        server_task.cancel()
