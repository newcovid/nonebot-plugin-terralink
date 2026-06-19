import asyncio
from typing import Any, Dict
from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, GroupMessageEvent
from nonebot.permission import SUPERUSER

from ..core.connection import manager, Session
from ..core.models import CommandResponsePacket

# --- 辅助函数 ---


async def get_session(matcher, event: GroupMessageEvent) -> Session:
    """获取会话，如果未连接则直接结束"""
    session = manager.get_session_by_group(event.group_id)
    if not session or not session.is_ready:
        await matcher.finish("当前群未绑定 TML 服务器或服务器未连接")
    return session


async def execute_and_reply(
    matcher, session: Session, command: str, args: list = None, timeout: float = 10.0
) -> Dict[str, Any]:
    """
    通用执行器：发送指令 -> 等待结果 -> 处理错误 -> 返回 data 字典
    """
    try:
        # 这里的 execute_command 已经是线程安全且带 ID 匹配的了
        response: CommandResponsePacket = await session.execute_command(
            command, args, timeout
        )
    except asyncio.TimeoutError:
        await matcher.finish("请求超时：服务器响应过慢。")
    except Exception as e:
        await matcher.finish(f"请求异常: {e}")

    if response.status != "success":
        # 如果服务器返回 error 状态，直接报错
        err_msg = response.message or "未知错误"
        await matcher.finish(f"操作失败: {err_msg}")

    # 返回 data 字典 (可能是 None，转为空字典防止报错)
    return response.data if isinstance(response.data, dict) else {}


# =============================================================================
# 指令实现
# =============================================================================

# --- 1. 踢人 (Kick) ---
kick = on_command("kick", priority=5, permission=SUPERUSER, block=True)


@kick.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    # 解析: /kick <player> [reason]
    params = args.extract_plain_text().strip().split()
    if not params:
        await kick.finish("用法: /kick <玩家名> [原因]")

    # [修复] 移除之前的补丁代码，C# 端已能正确处理缺省参数

    session = await get_session(kick, event)
    data = await execute_and_reply(kick, session, "kick", params)

    # 解析返回数据
    target = data.get("target", "未知")
    reason = data.get("reason", "无")
    await kick.finish(f"已踢出玩家 [{target}]\n原因: {reason}")


# --- 2. 杀怪 (Butcher) ---
butcher = on_command("butcher", priority=5, permission=SUPERUSER, block=True)


@butcher.handle()
async def _(event: GroupMessageEvent):
    session = await get_session(butcher, event)
    data = await execute_and_reply(butcher, session, "butcher")

    # [Update] 匹配文档 6.12: killedCount
    count = data.get("killedCount", 0)
    await butcher.finish(f"已清理 {count} 个敌对生物。")


# --- 3. 给予物品 (Give) ---
give = on_command("give", priority=5, permission=SUPERUSER, block=True)


@give.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    # 解析: /give <player> <item> [amount]
    params = args.extract_plain_text().strip().split()
    if len(params) < 2:
        await give.finish("用法: /give <玩家> <物品名> [数量]")

    # [Fix] 自动补全数量
    if len(params) == 2:
        params.append("1")

    session = await get_session(give, event)
    data = await execute_and_reply(give, session, "give", params)

    player = data.get("player", params[0])
    item_name = data.get("item", params[1])
    amount = data.get("amount", 1)

    await give.finish(f"已给予 {player} {amount} 个 [{item_name}]。")


# --- 4. 给予Buff (Buff) ---
buff = on_command("buff", priority=5, permission=SUPERUSER, block=True)


@buff.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    # 解析: /buff <player/all> <buff> [sec]
    params = args.extract_plain_text().strip().split()
    if len(params) < 2:
        await buff.finish("用法: /buff <玩家/all> <Buff名> [秒数]")

    # [Fix] 自动补全时间 (默认 60 秒)
    if len(params) == 2:
        params.append("60")

    session = await get_session(buff, event)
    data = await execute_and_reply(buff, session, "buff", params)

    targets = data.get("targets", [])
    if isinstance(targets, list):
        targets_str = ", ".join(targets)
    else:
        targets_str = str(targets)

    buff_name = data.get("buff", "未知Buff")
    duration = data.get("duration", 0)

    await buff.finish(f"已给予 {targets_str} 效果: {buff_name} ({duration}秒)。")


# --- 5. 保存世界 (Save) ---
save = on_command("save", priority=5, permission=SUPERUSER, block=True)


@save.handle()
async def _(event: GroupMessageEvent):
    session = await get_session(save, event)
    # save 指令通常较慢，稍微增加超时
    await execute_and_reply(save, session, "save", timeout=20.0)
    await save.finish("世界存档已成功保存。")


# --- 6. 沉降液体 (Settle) ---
settle = on_command("settle", priority=5, permission=SUPERUSER, block=True)


@settle.handle()
async def _(event: GroupMessageEvent):
    session = await get_session(settle, event)
    await execute_and_reply(settle, session, "settle", timeout=30.0)
    await settle.finish("液体沉降计算完成。")


# --- 7. 修改/查询时间 (Time) ---
time_cmd = on_command("time", priority=5, permission=SUPERUSER, block=True)


@time_cmd.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    # 解析: /time [dawn/noon/dusk/midnight]
    # 如果无参则是查询，有参则是设置
    raw_args = args.extract_plain_text().strip().split()

    params = []
    if raw_args:
        # 如果有参数，自动补全 "set" 动作，适配模组逻辑
        # 用户输入: /time dawn -> 发送: ["set", "dawn"]
        val = raw_args[0].lower()
        if val in ["dawn", "noon", "dusk", "midnight", "morning", "night"]:
            params = ["set", val]
        else:
            # 如果用户已经输入了 set (比如 /time set dawn)，则透传
            params = raw_args

    session = await get_session(time_cmd, event)
    data = await execute_and_reply(time_cmd, session, "time", params)

    # [Update] 匹配文档 6.3: timeString, isDay, moonPhase
    time_str = data.get("timeString", "??:??")
    is_day = "白天" if data.get("isDay") else "夜晚"
    phase = data.get("moonPhase", "")
    action = data.get("action", "query")

    if action == "set":
        await time_cmd.finish(f"时间已修改为: {time_str} ({is_day})")
    else:
        await time_cmd.finish(f"当前时间: {time_str} ({is_day})\n月相: {phase}")


# --- 8. 资源导出 (ExportAssets) ---
export = on_command(
    "export", aliases={"exportassets"}, priority=5, permission=SUPERUSER, block=True
)


@export.handle()
async def _(event: GroupMessageEvent):
    # 直接拦截，不允许通过 Bot 远程执行
    msg = (
        "资源导出指令 (exportassets) 极其消耗服务器性能且耗时较长。\n"
        "为了防止服务器卡死或超时，请直接在服务器控制台或单人游戏中执行此指令。"
    )
    await export.finish(msg)


# --- 9. 原生指令透传 (Cmd) ---
raw_cmd = on_command("cmd", priority=5, permission=SUPERUSER, block=True)


@raw_cmd.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    msg = args.extract_plain_text().strip()
    if not msg:
        await raw_cmd.finish("用法: /cmd <指令> [参数]")

    parts = msg.split()
    session = await get_session(raw_cmd, event)

    # 透传指令也应该有回显
    response: CommandResponsePacket = await session.execute_command(parts[0], parts[1:])

    status_icon = "OK" if response.status == "success" else "ERR"
    reply = f"{status_icon} [{response.status}] {response.message}"

    await raw_cmd.finish(reply)
