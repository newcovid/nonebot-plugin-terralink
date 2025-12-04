from nonebot.plugin import PluginMetadata

from .config import Config

# 导入 Server 以注册生命周期钩子
from .core import server

# 导入 Matchers 以注册指令和事件响应
from .matchers import admin, query, chat

__plugin_meta__ = PluginMetadata(
    name="TerraLink",
    description="泰拉瑞亚 TModLoader 群服互通插件",
    usage=(
        "【管理指令 (SuperUser)】\n"
        "/kick, /butcher, /give, /buff, /save, /settle, /time, /cmd\n\n"
        "【查询指令】\n"
        "/list, /tps, /boss, /inv, /search, /query, /help"
    ),
    type="application",
    homepage="https://github.com/newcovid/nonebot-plugin-terralink",
    config=Config,
    supported_adapters={"~onebot.v11"},
)
