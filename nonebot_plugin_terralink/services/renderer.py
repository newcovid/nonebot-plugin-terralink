import os
import jinja2
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Set
from nonebot import get_plugin_config, require
from nonebot.log import logger

# 尝试导入 htmlrender 核心功能
try:
    require("nonebot_plugin_htmlrender")
    # 我们改用 get_new_page 来手动控制截图逻辑
    from nonebot_plugin_htmlrender import get_new_page

    HTMLRENDER_AVAILABLE = True
except Exception:
    HTMLRENDER_AVAILABLE = False

    async def get_new_page(*args, **kwargs):
        raise RuntimeError("htmlrender not available")


from ..config import Config
from ..core.models import (
    PlayerInventoryDto,
    SearchResultDto,
    ItemDetailDto,
    RecipeDataDto,
    BossProgressDto,
    PlayerListDto,
    TpsDto,
)

plugin_config = get_plugin_config(Config)
PLUGIN_DIR = Path(__file__).parent.parent
TEMPLATE_DIR = PLUGIN_DIR / "resources" / "templates"
CSS_DIR = PLUGIN_DIR / "resources" / "css"


class RendererService:
    def __init__(self):
        # 初始化 Jinja2 环境
        # 使用 FileSystemLoader 加载 TEMPLATE_DIR 下的模板
        # enable_async=True 意味着必须使用 render_async
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
            enable_async=True,
            autoescape=True,
        )

    @property
    def is_enabled(self) -> bool:
        return HTMLRENDER_AVAILABLE

    def _get_image_url(self, relative_path: Optional[str]) -> str:
        if not relative_path:
            return ""
        resource_root = plugin_config.terralink_resource_path
        if not resource_root:
            return ""
        try:
            return (
                (Path(resource_root).expanduser().resolve() / relative_path)
                .resolve()
                .as_uri()
            )
        except Exception:
            return ""

    async def _render(
        self, template_name: str, data: Any, extra_context: Dict = None
    ) -> bytes:
        if not self.is_enabled:
            raise RuntimeError("Renderer is not enabled")

        # 1. 动态视口策略
        # 默认宽度 1000px，高度给一个小值让其自适应
        viewport_width = 1000
        viewport_height = 100

        # 合成树横向内容较多，给更宽的画布
        if template_name == "recipe.html":
            viewport_width = 3000
            viewport_height = 600

        # 2. 准备渲染上下文
        render_context = {
            "img_root": self._get_image_url(""),
            "css_path": CSS_DIR.as_uri(),
            "data": data,
            "to_img_url": self._get_image_url,
            **(extra_context or {}),
        }

        # 3. Jinja2 渲染 HTML 字符串
        try:
            template = self.jinja_env.get_template(template_name)
            # 使用 await render_async 避免 asyncio.run() 冲突
            html_content = await template.render_async(**render_context)
        except Exception as e:
            logger.error(f"[TerraLink] Template Render Error: {e}")
            raise

        # 4. Playwright 截图
        async with get_new_page(
            viewport={"width": viewport_width, "height": viewport_height}
        ) as page:

            # [关键修复] 设置文件访问上下文 (Base URL)
            # 原因：如果在 about:blank (默认) 页面 set_content，浏览器安全策略会拦截 file:// 协议的 CSS 和图片加载。
            # 解决：必须先 navigate (goto) 到本地文件目录，确立 file:// 源信任关系。
            base_url = TEMPLATE_DIR.absolute().as_uri()
            try:
                await page.goto(base_url)
            except Exception as e:
                # 即使 goto 目录失败（例如没有 index.html），Context 通常也已建立，记录日志但继续尝试渲染
                logger.debug(
                    f"[TerraLink] Page goto base_url warning (usually harmless): {e}"
                )

            # 设置页面内容 (wait_until="networkidle" 等待图片/CSS加载完毕)
            await page.set_content(html_content, wait_until="networkidle")

            try:
                # 使用选择器定位到 .tml-panel 元素
                # 这样可以只截取面板部分，去除多余的背景空白，实现自适应宽度
                elem = await page.wait_for_selector(".tml-panel", timeout=5000)
                return await elem.screenshot(type="png")
            except Exception as e:
                # 如果找不到元素 (通常不会发生)，回退到全页截图
                logger.warning(
                    f"[TerraLink] Selector .tml-panel failed, fallback to full page: {e}"
                )
                return await page.screenshot(full_page=True, type="png")

    # --- 业务逻辑 (保持不变) ---

    async def render_inventory(self, data: PlayerInventoryDto) -> bytes:
        return await self._render("inventory.html", data.model_dump())

    async def render_search(self, data: SearchResultDto) -> bytes:
        return await self._render("search.html", data.model_dump())

    async def render_detail(self, data: ItemDetailDto) -> bytes:
        return await self._render("detail.html", data.model_dump())

    def _process_recipe_tree(self, data: RecipeDataDto) -> Dict:
        nodes = data.nodes
        all_recipes = data.craftRecipes
        recipe_map: Dict[int, List] = {}
        for r in all_recipes:
            if r.resultId not in recipe_map:
                recipe_map[r.resultId] = []
            recipe_map[r.resultId].append(r)

        def build_node(item_id: int, path: Set[int], depth: int) -> Dict:
            if depth > 20:
                return None

            if item_id in path:
                node_info = nodes.get(str(item_id))
                return {
                    "item": self._clean_node(item_id, node_info),
                    "recipes": [],
                    "is_leaf": True,
                }

            node_info = nodes.get(str(item_id))
            clean_node = self._clean_node(item_id, node_info)
            new_path = path | {item_id}

            tree_node = {"item": clean_node, "recipes": [], "is_leaf": True}
            recipes = recipe_map.get(item_id, [])

            if recipes:
                target_recipe = recipes[0]
                recipe_obj = {
                    "stations": [s.model_dump() for s in target_recipe.stations],
                    "conditions": target_recipe.conditions,
                    "ingredients": [],
                }

                # 循环截断检测
                for ing in target_recipe.ingredients:
                    if self._is_trivial_loop(ing.itemId, recipe_map, new_path):
                        continue

                    sub_tree = build_node(ing.itemId, new_path, depth + 1)
                    if sub_tree:
                        sub_tree["item"]["stack"] = ing.count
                        recipe_obj["ingredients"].append({"tree": sub_tree})

                if recipe_obj["ingredients"] or not target_recipe.ingredients:
                    tree_node["recipes"].append(recipe_obj)
                    tree_node["is_leaf"] = False

            return tree_node

        root_tree = build_node(data.targetId, set(), 0)

        MAX_USAGES = 50
        usage_recipes_all = data.usageRecipes
        usage_recipes_display = usage_recipes_all
        hidden_count = 0
        if len(usage_recipes_all) > MAX_USAGES:
            usage_recipes_display = usage_recipes_all[:MAX_USAGES]
            hidden_count = len(usage_recipes_all) - MAX_USAGES

        return {
            "root": root_tree,
            "usageRecipes": [r.model_dump() for r in usage_recipes_display],
            "hiddenUsagesCount": hidden_count,
            "nodes": {k: v.model_dump() for k, v in nodes.items()},
            "targetId": data.targetId,
        }

    def _is_trivial_loop(self, item_id: int, recipe_map: Dict, path: Set[int]) -> bool:
        recipes = recipe_map.get(item_id, [])
        if not recipes:
            return False
        first_recipe = recipes[0]
        if not first_recipe.ingredients:
            return False
        for ing in first_recipe.ingredients:
            if ing.itemId not in path:
                return False
        return True

    def _clean_node(self, item_id: int, node_info: Any) -> Dict:
        if not node_info:
            return {
                "id": item_id,
                "name": f"Unknown({item_id})",
                "imagePath": None,
                "mod": "Unknown",
                "stack": 1,
                "frameCount": 1,
            }
        return {
            "id": node_info.id,
            "name": node_info.name,
            "imagePath": node_info.imagePath,
            "mod": node_info.mod,
            "stack": 1,
            "frameCount": node_info.frameCount,
        }

    async def render_recipe(self, data: RecipeDataDto) -> bytes:
        processed_data = self._process_recipe_tree(data)
        return await self._render("recipe.html", processed_data)

    async def render_boss(self, data: BossProgressDto) -> bytes:
        return await self._render("boss.html", data.model_dump())

    async def render_list(self, data: PlayerListDto) -> bytes:
        return await self._render("list.html", data.model_dump())

    async def render_tps(self, data: TpsDto) -> bytes:
        return await self._render("tps.html", data.model_dump())

    async def render_help(self, commands: List[Dict[str, str]]) -> bytes:
        return await self._render("help.html", commands)


renderer = RendererService()
