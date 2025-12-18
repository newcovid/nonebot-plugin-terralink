import asyncio
import traceback
import io
import time
from pathlib import Path
from typing import Any, List
from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, GroupMessageEvent, MessageSegment, Bot
from nonebot.log import logger
from nonebot.exception import FinishedException
from nonebot.matcher import Matcher

# 尝试导入 PIL 用于图片尺寸检查
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
    CommandHelpDto,
)
from ..services.renderer import renderer

# =============================================================================
# 辅助函数
# =============================================================================


async def get_session(matcher: Matcher, event: GroupMessageEvent) -> Session:
    """获取会话，如果失败则回复提示"""
    session = manager.get_session_by_group(event.group_id)
    if not session or not session.is_ready:
        await matcher.finish("❌ 未连接到服务器，请检查游戏端状态。")
    return session


async def execute_query(
    matcher: Matcher, session: Session, command: str, args: list = None
) -> Any:
    """通用查询执行器"""
    try:
        response = await session.execute_command(command, args, timeout=30.0)
    except asyncio.TimeoutError:
        await matcher.finish("⚠️ 查询超时，请稍后再试。")
    except Exception as e:
        await matcher.finish(f"⚠️ 查询异常: {e}")

    if response.status != "success":
        await matcher.finish(f"❌ 查询失败: {response.message}")

    return response.data


async def render_and_finish(
    bot: Bot, matcher: Matcher, event: GroupMessageEvent, render_func, data
):
    """
    通用渲染并结束 Matcher 的流程
    [Update] 增加了 bot 和 event 参数，用于支持文件上传 API
    """
    img = None
    try:
        logger.debug(f"[TerraLink] 准备渲染数据类型: {type(data)}")
        # 1. 尝试渲染
        img = await render_func(data)
    except FinishedException:
        raise
    except Exception as e:
        # 2. 渲染失败处理
        err_trace = traceback.format_exc()
        logger.error(f"[TerraLink] 图片渲染未捕获异常:\n{err_trace}")

        await matcher.finish(
            f"⚠️ 图片渲染失败: {type(e).__name__} - {e}\n(详情请检查控制台日志)"
        )
        return

    # 3. 发送图片 (智能判断是否转为文件)
    if img:
        try:
            should_send_as_file = False
            file_name = f"terralink_{int(time.time())}.png"

            # 尺寸阈值：单边超过 6000px 或 体积超过 4MB
            SIZE_LIMIT_PIXELS = 6000
            SIZE_LIMIT_BYTES = 4 * 1024 * 1024

            if len(img) > SIZE_LIMIT_BYTES:
                should_send_as_file = True
                logger.info(
                    f"[TerraLink] 图片体积过大 ({len(img)/1024:.2f}KB)，转为文件发送"
                )

            elif PIL_AVAILABLE:
                try:
                    with Image.open(io.BytesIO(img)) as pil_img:
                        w, h = pil_img.size
                        if w > SIZE_LIMIT_PIXELS or h > SIZE_LIMIT_PIXELS:
                            should_send_as_file = True
                            logger.info(
                                f"[TerraLink] 图片尺寸过大 ({w}x{h})，转为文件发送"
                            )
                except Exception as e:
                    logger.warning(f"[TerraLink] PIL check failed: {e}")

            if should_send_as_file:
                # OneBot V11 没有 MessageSegment.file，必须使用 upload_group_file API
                # 并且通常需要传入本地路径

                # 1. 准备临时目录
                temp_dir = Path("data/terralink/temp")
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_file = temp_dir / file_name

                try:
                    # 2. 写入文件
                    temp_file.write_bytes(img)
                    abs_path = temp_file.resolve()

                    await matcher.send("⚠️ 图片过大，正在以文件形式上传...")

                    # 3. 调用 API 上传
                    await bot.upload_group_file(
                        group_id=event.group_id, file=str(abs_path), name=file_name
                    )
                except Exception as e:
                    logger.error(f"[TerraLink] 文件上传API调用失败: {e}")
                    await matcher.finish(f"⚠️ 文件上传失败: {e}")
                finally:
                    # 4. 清理临时文件
                    if temp_file.exists():
                        try:
                            temp_file.unlink()
                        except Exception:
                            pass
            else:
                # 正常发送图片
                await matcher.finish(MessageSegment.image(img))

        except FinishedException:
            raise
        except Exception as e:
            logger.error(f"[TerraLink] 发送失败: {e}")
            await matcher.finish(f"⚠️ 发送失败: {e}")
    else:
        await matcher.finish("⚠️ 渲染结果为空 (Template returned None)")


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
        await inv_cmd.finish("❌ 未找到该玩家或数据为空")

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
        await query_cmd.finish("❌ 未找到物品 (请尝试用ID或完整名称)")

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
        await recipe_cmd.finish("❌ 未找到物品或无合成数据")

    data = RecipeDataDto(**raw_data)
    await render_and_finish(bot, recipe_cmd, event, renderer.render_recipe, data)
