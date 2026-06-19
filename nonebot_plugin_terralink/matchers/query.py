import asyncio
import base64
import io
import time
import traceback
from typing import Any
from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, GroupMessageEvent, MessageSegment, Bot
from nonebot.log import logger
from nonebot.exception import FinishedException
from nonebot.matcher import Matcher

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    Image = None
    PIL_AVAILABLE = False

from ..core.connection import manager, Session
from ..core.models import (
    PlayerListDto,
    TpsDto,
    BossProgressDto,
    PlayerInventoryDto,
    SearchResultDto,
    ItemDetailDto,
    RecipeDataDto,
)
from ..services.renderer import renderer

# =============================================================================
# 辅助函数
# =============================================================================


async def get_session(matcher: Matcher, event: GroupMessageEvent) -> Session:
    """获取会话，如果失败则回复提示"""
    session = manager.get_session_by_group(event.group_id)
    if not session or not session.is_ready:
        await matcher.finish("未连接到服务器，请检查游戏端状态。")
    return session


async def execute_query(
    matcher: Matcher, session: Session, command: str, args: list = None
) -> Any:
    """通用查询执行器"""
    try:
        response = await session.execute_command(command, args, timeout=30.0)
    except asyncio.TimeoutError:
        await matcher.finish("查询超时，请稍后再试。")
    except Exception as e:
        await matcher.finish(f"查询异常: {e}")

    if response.status != "success":
        await matcher.finish(f"查询失败: {response.message}")

    return response.data


# 单边像素超过此值判定为大图，转为文件发送
SIZE_LIMIT_PIXELS = 6000
# 字节超过此值判定为大图（QQ 单图风控阈值附近）
SIZE_LIMIT_BYTES = 4 * 1024 * 1024


def _should_send_as_file(img: bytes) -> bool:
    if len(img) > SIZE_LIMIT_BYTES:
        logger.info(
            f"[TerraLink] 图片体积过大 ({len(img) / 1024:.2f}KB)，转为文件发送"
        )
        return True

    if PIL_AVAILABLE:
        try:
            with Image.open(io.BytesIO(img)) as pil_img:
                w, h = pil_img.size
                if w > SIZE_LIMIT_PIXELS or h > SIZE_LIMIT_PIXELS:
                    logger.info(f"[TerraLink] 图片尺寸过大 ({w}x{h})，转为文件发送")
                    return True
        except Exception as e:
            logger.warning(f"[TerraLink] PIL check failed: {e}")

    return False


async def render_and_finish(
    bot: Bot, matcher: Matcher, event: GroupMessageEvent, render_func, data
):
    """
    通用渲染并发送的流程。
    渲染产物始终保留在内存中：
      - 普通图片：MessageSegment.image(bytes) 内部会编码为 base64://
      - 大图：upload_group_file 接收 base64:// URI，避免依赖本地磁盘路径
    这样异地部署的 napcat / Lagrange 也能正常读取，无需共享文件系统。
    """
    try:
        img = await render_func(data)
    except FinishedException:
        raise
    except Exception as e:
        logger.error(f"[TerraLink] 图片渲染未捕获异常:\n{traceback.format_exc()}")
        await matcher.finish(
            f"图片渲染失败: {type(e).__name__} - {e}\n(详情请检查控制台日志)"
        )
        return

    if not img:
        await matcher.finish("渲染结果为空 (Template returned None)")
        return

    try:
        if _should_send_as_file(img):
            file_name = f"terralink_{int(time.time())}.png"
            file_uri = "base64://" + base64.b64encode(img).decode("ascii")
            await matcher.send("图片过大，正在以文件形式上传...")
            try:
                await bot.upload_group_file(
                    group_id=event.group_id, file=file_uri, name=file_name
                )
            except Exception as e:
                logger.error(f"[TerraLink] 文件上传API调用失败: {e}")
                await matcher.finish(f"文件上传失败: {e}")
        else:
            await matcher.finish(MessageSegment.image(img))
    except FinishedException:
        raise
    except Exception as e:
        logger.error(f"[TerraLink] 发送失败: {e}")
        await matcher.finish(f"发送失败: {e}")


# =============================================================================
# 指令实现
# =============================================================================

# --- 1. 帮助 (Help) ---
help_cmd = on_command("help", aliases={"帮助", "菜单"}, priority=10, block=True)


@help_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    session = await get_session(help_cmd, event)
    raw_data = await execute_query(help_cmd, session, "help")

    # 数据兼容处理
    commands_data = raw_data
    if isinstance(raw_data, dict) and "commands" in raw_data:
        commands_data = raw_data["commands"]

    commands_list = []
    if isinstance(commands_data, list):
        for cmd in commands_data:
            if isinstance(cmd, dict):
                commands_list.append(cmd)
            else:
                commands_list.append({"name": str(cmd), "description": "", "usage": ""})

    await render_and_finish(bot, help_cmd, event, renderer.render_help, commands_list)


# --- 2. 在线列表 (List) ---
list_cmd = on_command("list", aliases={"在线", "who", "ls"}, priority=10, block=True)


@list_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    session = await get_session(list_cmd, event)
    raw_data = await execute_query(list_cmd, session, "list")
    data = PlayerListDto(**raw_data)
    await render_and_finish(bot, list_cmd, event, renderer.render_list, data)


# --- 3. 性能 (TPS) ---
tps_cmd = on_command("tps", aliases={"status", "性能"}, priority=10, block=True)


@tps_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    session = await get_session(tps_cmd, event)
    raw_data = await execute_query(tps_cmd, session, "tps")
    data = TpsDto(**raw_data)
    await render_and_finish(bot, tps_cmd, event, renderer.render_tps, data)


# --- 4. Boss进度 (Boss) ---
boss_cmd = on_command("boss", aliases={"bosses", "进度"}, priority=10, block=True)


@boss_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    session = await get_session(boss_cmd, event)
    raw_data = await execute_query(boss_cmd, session, "boss")
    data = BossProgressDto(**raw_data)
    await render_and_finish(bot, boss_cmd, event, renderer.render_boss, data)


# --- 5. 查背包 (Inv) ---
inv_cmd = on_command("inv", aliases={"inventory", "查背包"}, priority=10, block=True)


@inv_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    params = args.extract_plain_text().strip().split()
    if not params:
        await inv_cmd.finish("用法: /inv <玩家名>")

    session = await get_session(inv_cmd, event)
    raw_data = await execute_query(inv_cmd, session, "inv", params)

    if not raw_data:
        await inv_cmd.finish("未找到该玩家或数据为空")

    data = PlayerInventoryDto(**raw_data)
    await render_and_finish(bot, inv_cmd, event, renderer.render_inventory, data)


# --- 6. 搜索 (Search) ---
search_cmd = on_command("search", aliases={"搜索", "查找"}, priority=10, block=True)


@search_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    params = args.extract_plain_text().strip().split()
    if not params:
        await search_cmd.finish("用法: /search <关键词>")

    session = await get_session(search_cmd, event)
    raw_data = await execute_query(search_cmd, session, "search", params)
    data = SearchResultDto(**raw_data)
    await render_and_finish(bot, search_cmd, event, renderer.render_search, data)


# --- 7. 查询详情 (Query) ---
query_cmd = on_command("query", aliases={"查询", "属性"}, priority=10, block=True)


@query_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    params = args.extract_plain_text().strip().split()
    if not params:
        await query_cmd.finish("用法: /query <物品名或ID>")

    session = await get_session(query_cmd, event)
    raw_data = await execute_query(query_cmd, session, "query", params)

    if not raw_data:
        await query_cmd.finish("未找到物品 (请尝试用ID或完整名称)")

    data = ItemDetailDto(**raw_data)
    await render_and_finish(bot, query_cmd, event, renderer.render_detail, data)


# --- 8. 合成树 (Recipe) ---
recipe_cmd = on_command("recipe", aliases={"合成", "配方"}, priority=10, block=True)


@recipe_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    params = args.extract_plain_text().strip().split()
    if not params:
        await recipe_cmd.finish("用法: /recipe <物品名或ID>")

    session = await get_session(recipe_cmd, event)
    raw_data = await execute_query(recipe_cmd, session, "recipe", params)

    if not raw_data:
        await recipe_cmd.finish("未找到物品或无合成数据")

    data = RecipeDataDto(**raw_data)
    await render_and_finish(bot, recipe_cmd, event, renderer.render_recipe, data)
