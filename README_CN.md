[中文 README](README_CN.md) | [English README](README.md) | [中文通信文档](TerraNoneBridge通信文档.md) | [English Protocol](TerraNoneBridge_Protocol.md)

<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-terralink

_✨ 泰拉瑞亚 TModLoader 服务器与 QQ 群双向互通的 NoneBot2 插件 ✨_

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/newcovid/nonebot-plugin-terralink.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-terralink">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-terralink.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">

</div>

## 📖 介绍

**TerraLink** 是一个 NoneBot2 插件，用于实现泰拉瑞亚 TModLoader 服务器与 QQ 群的双向互通。通过 WebSocket 协议连接 TML 模组客户端，将游戏内的聊天消息、事件通知同步到 QQ 群，同时支持从 QQ 群发送指令到游戏服务器进行管理操作、查询物品合成表、查看玩家背包等高级功能。

### 核心特性

- 🔗 **双向通信**：游戏消息 ↔ QQ 群消息实时同步
- 🎨 **富文本渲染**：基于 HTML/CSS 的精美图片回复（物品详情、背包、合成树等）
- 🎮 **完整的指令系统**：支持 16+ 个服务器管理和查询指令
- 🔐 **安全的认证机制**：Token-based 鉴权系统
- 📱 **多服务器支持**：一个 Bot 可同时管理多个 TML 服务器
- 🚀 **高效架构**：基于 asyncio 和 websockets 的高性能实现

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>

在 nonebot2 项目的根目录下打开命令行，输入以下指令即可安装

```bash
nb plugin install nonebot-plugin-terralink
```

</details>

<details>
<summary>使用包管理器安装</summary>

在 nonebot2 项目的插件目录下，打开命令行，根据你使用的包管理器，输入相应的安装命令

<details>
<summary>pip</summary>

```bash
pip install nonebot-plugin-terralink
```

</details>

</details>

## ⚙️ 配置

在 NoneBot 的 `.env` 或 `.env.prod` 文件中配置以下选项：

```env
# 插件总开关
terralink_enabled=true

# WebSocket 监听端口 (TModLoader 端连接此端口)
terralink_port=7778

# 指令前缀 (用于 QQ 群内识别指令)
terralink_cmd_prefix=/

# 资源路径 (必选, 用于加载本地纹理)
# 资源获得方式:只能通过在游戏客户端安装 TerraNoneBridge 模组获取,首先配置模组配置项"自定义导出路径",
# "自定义导出路径"示例为:"D:\desktop\temp\tmodass",需要为资源导出创建一个空文件夹,例如tmodass,这样资源才不会散乱的释放到上级目录中.
# 在单人模式或本地主机模式下使用"/tnb exportassets"指令导出资源,并将资源手动放置到服务器可访问的位置
# 示例:"/www/program/nonebot2/lolbot/data/terralink/tmodass"或"data/terralink/tmodass"
terralink_resource_path=""

# 多服务器映射列表 (JSON 格式)
terralink_links=[
    {"token": "your_secret_token_1", "group_id": 123456789, "name": "生存服"},
    {"token": "your_secret_token_2", "group_id": 987654321, "name": "灾厄服"}
]
```

---

## 💻 指令列表

### 1. 管理指令 (仅 SuperUser 可用)

#### 💀 `boss`
查看当前世界的 Boss 击杀进度。
- **指令**: `/boss`
- **别名**: `bosses`, `进度`

![boss效果图](/imgs/boss.png)

#### 💊 `buff`
给予指定玩家或全体玩家 Buff。
- **指令**: `/buff <玩家/all> <Buff名> [秒数]`

![buff效果图](/imgs/buff.png)

#### 🗡️ `butcher`
清理服务器内所有敌对生物（杀怪）。
- **指令**: `/butcher`

![butcher效果图](/imgs/butcher.png)

#### 📤 `exportassets`
导出游戏内的资源（纹理等），这是一个耗时操作，通常在服务器后台执行。Bot 端会拦截此指令以防误触。
- **指令**: `/export` 或 `/exportassets`


#### 🎁 `give`
给予指定玩家物品。
- **指令**: `/give <玩家> <物品名> [数量]`

![give效果图](/imgs/give.png)

#### 🦵 `kick`
踢出指定玩家。
- **指令**: `/kick <玩家名> [原因]`

![kick效果图](/imgs/kick.png)

#### 💾 `save`
强制保存世界存档。
- **指令**: `/save`

![save效果图](/imgs/save.png)

#### 💧 `settle`
强制沉降世界内的所有液体。
- **指令**: `/settle`

![settle效果图](/imgs/settle.png)

#### ⏰ `time`
查询或修改世界时间。
- **指令**: `/time [dawn/noon/dusk/midnight]`
- **说明**: 不带参数为查询时间，带参数为设置时间。

![time效果图](/imgs/time.png)

---

### 2. 查询指令 (所有用户可用)

#### 📖 `help`
显示指令帮助菜单。
- **指令**: `/help`
- **别名**: `帮助`, `菜单`

![help效果图](/imgs/help.png)

#### 🎒 `inv`
查看指定玩家的背包、装备和饰品栏。
- **指令**: `/inv <玩家名>`
- **别名**: `inventory`, `查背包`

![inv效果图](/imgs/inv.png)

#### 👥 `list`
查看当前在线玩家列表。
- **指令**: `/list`
- **别名**: `在线`, `who`, `ls`

![list效果图](/imgs/list.png)

#### 🔍 `query`
查询物品详细信息（属性、掉落、售卖NPC、简易合成）。
- **指令**: `/query <物品名或ID>`
- **别名**: `查询`, `属性`

![query效果图](/imgs/query.png)

#### 🔨 `recipe`
生成物品的完整合成树图片，包含所有前置材料。
- **指令**: `/recipe <物品名或ID>`
- **别名**: `合成`, `配方`

![recipe效果图](/imgs/recipe.png)

#### 🔎 `search`
模糊搜索物品名称，返回匹配结果列表。
- **指令**: `/search <关键词>`
- **别名**: `搜索`, `查找`

![search效果图](/imgs/search.png)

#### 📊 `tps`
查看服务器性能状态（TPS、内存、实体数量等）。
- **指令**: `/tps`
- **别名**: `status`, `性能`

![tps效果图](/imgs/tps.png)

---

## 💰 赞助与支持

如果您觉得这个插件对您有帮助，欢迎请作者喝一杯咖啡 ☕

<div align="center">
  <img src="/imgs/wechat.png" width="200" alt="微信支付">
  <img src="/imgs/alipay.png" width="200" alt="支付宝支付">
</div>

## 📄 许可证

本项目遵循 [MIT License](LICENSE) 开源。