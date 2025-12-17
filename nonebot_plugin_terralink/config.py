from pydantic import BaseModel, Extra
from typing import List, Optional


class LinkConfig(BaseModel):
    """
    单组连接配置：定义一个 TML 服务器与一个 QQ 群的绑定关系
    """

    # TML 端配置的 AccessToken，作为唯一识别码
    token: str
    # 绑定的 QQ 群号
    group_id: int
    # 服务器名称（用于日志和消息前缀区分）
    name: str = "Terraria Server"


class Config(BaseModel, extra=Extra.ignore):
    # 插件总开关
    terralink_enabled: bool = True

    # WebSocket 监听端口 (所有 TML 客户端都连接到这个端口)
    terralink_port: int = 7778

    # [核心] 多服务器映射列表
    # 示例:
    # [
    #   {"token": "server_survival", "group_id": 11111, "name": "生存服"},
    #   {"token": "server_calamity", "group_id": 22222, "name": "灾厄服"}
    # ]
    terralink_links: List[LinkConfig] = []

    # 指令前缀 (用于 QQ 发消息转为游戏指令的标识，如 /say)
    terralink_cmd_prefix: str = "/"

    # 用于存放从 exportassets 导出的图片，或手动解包的资源
    # 如果为空，则强制使用纯文本模式
    terralink_resource_path: Optional[str] = None
