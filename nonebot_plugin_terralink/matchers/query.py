from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, GroupMessageEvent

from ..core.connection import manager


async def get_session_or_reply(matcher, event: GroupMessageEvent):
    """尝试获取会话，如果失败则回复提示"""
    session = manager.get_session_by_group(event.group_id)
    if not session or not session.is_ready:
        # [修改] 不再静默失败，而是提示用户
        await matcher.finish("❌ 未连接到服务器，请检查游戏端状态。")
    return session


# --- 1. 帮助 ---
help_cmd = on_command("help", aliases={"帮助", "菜单"}, priority=10, block=True)


@help_cmd.handle()
async def _(event: GroupMessageEvent):
    session = await get_session_or_reply(help_cmd, event)
    await session.send_command("help")


# --- 2. 在线列表 ---
list_cmd = on_command("list", aliases={"在线", "who", "ls"}, priority=10, block=True)


@list_cmd.handle()
async def _(event: GroupMessageEvent):
    session = await get_session_or_reply(list_cmd, event)
    await session.send_command("list")


# --- 3. 性能 ---
tps_cmd = on_command("tps", aliases={"status", "性能"}, priority=10, block=True)


@tps_cmd.handle()
async def _(event: GroupMessageEvent):
    session = await get_session_or_reply(tps_cmd, event)
    await session.send_command("tps")


# --- 4. Boss ---
boss_cmd = on_command("boss", aliases={"bosses", "进度"}, priority=10, block=True)


@boss_cmd.handle()
async def _(event: GroupMessageEvent):
    session = await get_session_or_reply(boss_cmd, event)
    await session.send_command("boss")


# --- 5. 背包 ---
inv_cmd = on_command("inv", aliases={"inventory", "查背包"}, priority=10, block=True)


@inv_cmd.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    params = args.extract_plain_text().strip().split()
    if not params:
        await inv_cmd.finish("用法: /inv <玩家名>")

    session = await get_session_or_reply(inv_cmd, event)
    await session.send_command("inv", params)


# --- 6. 搜索 ---
search_cmd = on_command("search", aliases={"搜索", "查找"}, priority=10, block=True)


@search_cmd.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    params = args.extract_plain_text().strip().split()
    if not params:
        await search_cmd.finish("用法: /search <关键词>")

    session = await get_session_or_reply(search_cmd, event)
    await session.send_command("search", params)


# --- 7. 查询 ---
query_cmd = on_command("query", aliases={"查询", "合成"}, priority=10, block=True)


@query_cmd.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    params = args.extract_plain_text().strip().split()
    if not params:
        await query_cmd.finish("用法: /query <物品名或ID>")

    session = await get_session_or_reply(query_cmd, event)
    await session.send_command("query", params)
