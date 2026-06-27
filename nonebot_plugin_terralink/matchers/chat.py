from nonebot import on_message, get_plugin_config
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.log import logger
from nonebot.rule import Rule

from ..config import Config
from ..core.connection import manager

plugin_config = get_plugin_config(Config)


async def is_bound_group(event: GroupMessageEvent) -> bool:
    """
    Rule: 检查当前群是否在配置列表中 (不管是否已连接)
    """
    if not plugin_config.terralink_enabled:
        return False
    try:
        group_id = int(event.group_id)
    except (TypeError, ValueError):
        logger.warning(f"[TerraLink] 收到无效群号的群消息: {event.group_id!r}")
        return False
    return any(
        int(link.group_id) == group_id for link in plugin_config.terralink_links
    )


# 优先级设为 99，避免拦截其他指令
chat_forward = on_message(rule=Rule(is_bound_group), priority=99, block=False)


@chat_forward.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    # 1. 获取对应的 Session
    session = manager.get_session_by_group(event.group_id)

    # 未连接则忽略
    if not session or not session.is_ready:
        logger.debug(
            f"[TerraLink] 群 {event.group_id} 的消息未转发：未找到已认证的 TML 连接"
        )
        return

    # 2. 文本过滤
    text = event.get_plaintext().strip()
    if not text:
        return
    # 忽略可能是指令的消息
    if text.startswith(("/", "#", ".")):
        return

    # 3. 构造发送者名称 (优先使用群名片)
    user_name = event.sender.card or event.sender.nickname or str(event.user_id)

    # 4. 发送 Chat 包
    # 这里不需要 execute_command 等待回复，因为聊天是推流式的
    if not await session.send_chat(user_name, text):
        logger.warning(f"[TerraLink] 群 {event.group_id} 的消息发送到 TML 失败")
