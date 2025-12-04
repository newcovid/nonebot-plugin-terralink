from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, GroupMessageEvent
from nonebot.permission import SUPERUSER

from ..core.connection import manager


# --- 辅助：获取当前群对应的 Session ---
async def get_session(matcher, event: GroupMessageEvent):
    session = manager.get_session_by_group(event.group_id)
    if not session or not session.is_ready:
        await matcher.finish("❌ 当前群未绑定 TML 服务器或服务器未连接")
    return session


# --- 1. 踢人 (Kick) ---
kick = on_command("kick", priority=5, permission=SUPERUSER, block=True)


@kick.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    # 解析: /kick <player> [reason]
    params = args.extract_plain_text().strip().split()
    if not params:
        await kick.finish("用法: /kick <玩家名> [原因]")

    session = await get_session(kick, event)
    await session.send_command("kick", params)


# --- 2. 杀怪 (Butcher) ---
butcher = on_command("butcher", priority=5, permission=SUPERUSER, block=True)


@butcher.handle()
async def _(event: GroupMessageEvent):
    session = await get_session(butcher, event)
    await session.send_command("butcher")


# --- 3. 给予物品 (Give) ---
give = on_command("give", priority=5, permission=SUPERUSER, block=True)


@give.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    # 解析: /give <player> <item> [amount]
    params = args.extract_plain_text().strip().split()
    if len(params) < 2:
        await give.finish("用法: /give <玩家> <物品名> [数量]")

    session = await get_session(give, event)
    await session.send_command("give", params)


# --- 4. 给予Buff (Buff) ---
buff = on_command("buff", priority=5, permission=SUPERUSER, block=True)


@buff.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    # 解析: /buff <player/all> <buff> [sec]
    params = args.extract_plain_text().strip().split()
    if len(params) < 2:
        await buff.finish("用法: /buff <玩家/all> <Buff名> [秒数]")

    session = await get_session(buff, event)
    await session.send_command("buff", params)


# --- 5. 保存世界 (Save) ---
save = on_command("save", priority=5, permission=SUPERUSER, block=True)


@save.handle()
async def _(event: GroupMessageEvent):
    session = await get_session(save, event)
    await session.send_command("save")


# --- 6. 沉降液体 (Settle) ---
settle = on_command("settle", priority=5, permission=SUPERUSER, block=True)


@settle.handle()
async def _(event: GroupMessageEvent):
    session = await get_session(settle, event)
    await session.send_command("settle")


# --- 7. 修改时间 (Time) ---
time_cmd = on_command("time", priority=5, permission=SUPERUSER, block=True)


@time_cmd.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    # 解析: /time <dawn/noon/dusk/midnight>
    params = args.extract_plain_text().strip().split()
    if not params:
        await time_cmd.finish("用法: /time <dawn/noon/dusk/midnight>")

    session = await get_session(time_cmd, event)
    await session.send_command("time", params)


# --- 8. 原生指令透传 (Cmd) ---
raw_cmd = on_command("cmd", priority=5, permission=SUPERUSER, block=True)


@raw_cmd.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    msg = args.extract_plain_text().strip()
    if not msg:
        await raw_cmd.finish("用法: /cmd <指令> [参数]")

    parts = msg.split()
    session = await get_session(raw_cmd, event)
    await session.send_command(parts[0], parts[1:])
