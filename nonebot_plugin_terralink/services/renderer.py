import os
import jinja2
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Set, Tuple
from nonebot import get_plugin_config, require
from nonebot.log import logger

# [Fix] Jinja2 3.1+ 移除了 Markup 的直接导出，必须从 markupsafe 导入
try:
    from markupsafe import Markup
except ImportError:
    # 兼容旧版本环境
    from jinja2 import Markup

try:
    require("nonebot_plugin_htmlrender")
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

    def _format_coin(self, value: int) -> Markup:
        """
        将铜币数值格式化为 铂/金/银/铜 的 HTML 字符串。
        使用 Markup 包裹，防止 Jinja2 自动转义导致 HTML 源码直接显示在图片上。
        """
        if not value or value <= 0:
            return Markup('<span style="color:#888;">无价值</span>')

        platinum = value // 1_000_000
        rem = value % 1_000_000
        gold = rem // 10_000
        rem = rem % 10_000
        silver = rem // 100
        copper = rem % 100

        parts = []
        # 使用 white-space: nowrap 防止 数字和单位被换行分开
        style_base = "text-shadow: 1px 1px 0 #000; white-space: nowrap;"

        if platinum > 0:
            parts.append(
                f'<span style="color:#dcebf5; {style_base}">{platinum}铂</span>'
            )
        if gold > 0:
            parts.append(f'<span style="color:#e0c055; {style_base}">{gold}金</span>')
        if silver > 0:
            parts.append(f'<span style="color:#b5b8c0; {style_base}">{silver}银</span>')
        if copper > 0:
            parts.append(f'<span style="color:#c57a53; {style_base}">{copper}铜</span>')

        # 返回 Markup 对象，确保模板渲染时被视为 HTML 代码而非纯文本
        return Markup(" ".join(parts))

    async def _render(
        self, template_name: str, data: Any, extra_context: Dict = None
    ) -> bytes:
        if not self.is_enabled:
            raise RuntimeError("Renderer is not enabled")

        # 动态视口策略
        viewport_width = 1000
        viewport_height = 100

        if template_name == "recipe.html":
            viewport_width = 2400
            viewport_height = 600

        render_context = {
            "img_root": self._get_image_url(""),
            "css_path": CSS_DIR.as_uri(),
            "data": data,
            "to_img_url": self._get_image_url,
            "format_coin": self._format_coin,
            **(extra_context or {}),
        }

        try:
            template = self.jinja_env.get_template(template_name)
            html_content = await template.render_async(**render_context)
        except Exception as e:
            logger.error(f"[TerraLink] Template Render Error: {e}")
            raise

        async with get_new_page(
            viewport={"width": viewport_width, "height": viewport_height}
        ) as page:
            base_url = TEMPLATE_DIR.absolute().as_uri()
            try:
                await page.goto(base_url)
            except Exception:
                pass

            await page.set_content(html_content, wait_until="networkidle")

            try:
                elem = await page.wait_for_selector(".tml-panel", timeout=5000)
                return await elem.screenshot(type="png")
            except Exception as e:
                logger.warning(
                    f"[TerraLink] Selector .tml-panel failed, fallback to full page: {e}"
                )
                return await page.screenshot(full_page=True, type="png")

    # --- 业务逻辑 ---

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

        MAX_DEPTH = 50
        MAX_TOTAL_NODES = 2000

        current_node_count = 0
        target_id = data.targetId

        global_expanded_ids: Set[int] = set()

        def build_node(
            item_id: int, path: Set[int], depth: int
        ) -> Tuple[Optional[Dict], Set[int]]:
            nonlocal current_node_count

            if depth > MAX_DEPTH or current_node_count >= MAX_TOTAL_NODES:
                node_info = nodes.get(str(item_id))
                return {
                    "item": self._clean_node(item_id, node_info),
                    "recipes": [],
                    "is_leaf": True,
                    "truncated": True,
                }, set()

            current_node_count += 1
            node_info = nodes.get(str(item_id))

            if item_id in path:
                return {
                    "item": self._clean_node(item_id, node_info),
                    "recipes": [],
                    "is_leaf": True,
                    "loop": True,
                }, {item_id}

            if item_id in global_expanded_ids:
                return {
                    "item": self._clean_node(item_id, node_info),
                    "recipes": [],
                    "is_leaf": True,
                    "reference": True,
                }, set()

            global_expanded_ids.add(item_id)

            clean_node = self._clean_node(item_id, node_info)
            new_path = path | {item_id}
            tree_node = {"item": clean_node, "recipes": [], "is_leaf": True}
            detected_loops = set()

            recipes = recipe_map.get(item_id, [])
            if recipes:
                target_recipe = recipes[0]
                recipe_obj = {
                    "stations": [s.model_dump() for s in target_recipe.stations],
                    "conditions": target_recipe.conditions,
                    "ingredients": [],
                }

                has_ingredients = False
                for ing in target_recipe.ingredients:
                    sub_tree, sub_loops = build_node(ing.itemId, new_path, depth + 1)
                    detected_loops.update(sub_loops)

                    if sub_tree:
                        sub_tree["item"]["stack"] = ing.count
                        recipe_obj["ingredients"].append({"tree": sub_tree})
                        has_ingredients = True

                if has_ingredients or not target_recipe.ingredients:
                    tree_node["recipes"].append(recipe_obj)
                    tree_node["is_leaf"] = False

            if item_id in detected_loops:
                if item_id != target_id:
                    tree_node["recipes"] = []
                    tree_node["is_leaf"] = True
                    detected_loops.remove(item_id)

            return tree_node, detected_loops

        root_tree, _ = build_node(target_id, set(), 0)

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
