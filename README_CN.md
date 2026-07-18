[中文 README](README_CN.md) | [English README](README.md) | [中文通信文档](TerraNoneBridge通信文档.md) | [English Protocol](TerraNoneBridge_Protocol.md)

<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-terralink

_✨ 泰拉瑞亚 tModLoader 服务器与 QQ 群双向互通的 NoneBot2 插件 ✨_

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/newcovid/nonebot-plugin-terralink.svg" alt="license">
</a>
<a href="https://pypi.org/project/nonebot-plugin-terralink/">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-terralink.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">

</div>

## 📖 介绍

**TerraLink** 是一个 NoneBot2 插件，用于实现泰拉瑞亚 tModLoader 服务器与 QQ 群的双向互通。项目通过 WebSocket 协议连接配套的 TML 模组，将游戏内聊天和事件通知实时同步到 QQ 群，同时支持从 QQ 群向游戏服务器发送管理指令、查询物品合成表、查看玩家背包等功能。

### 核心特性

- 🔗 **双向通信**：游戏消息 ↔ QQ 群消息实时同步
- 🎨 **富文本渲染**：使用 HTML/CSS 渲染物品详情、背包、合成树等结构化信息
- 🎮 **完整指令系统**：支持 16+ 个服务器管理和查询指令
- 🔐 **安全认证机制**：Bot 与游戏服务器之间使用 Token 鉴权
- 📱 **多服务器支持**：一个 Bot 可同时管理多个 tModLoader 服务器
- 🚀 **异步架构**：基于 `asyncio` 和 `websockets` 实现

## 🌍 项目影响与生态价值

TerraLink 维护了一个连接三个不同生态的开源互操作层：**NoneBot2/OneBot 机器人、QQ 群社区和泰拉瑞亚 tModLoader 服务器**。项目解决的是单个生态自身无法完整覆盖的专业化集成需求。

- **公开发行**：Python 插件通过 [PyPI](https://pypi.org/project/nonebot-plugin-terralink/) 发布，配套的 `TerraNoneBridge` 模组通过 [Steam 创意工坊](https://steamcommunity.com/sharedfiles/filedetails/?id=3617766364) 分发。
- **实际运维范围**：项目覆盖双向聊天、事件转发、远程管理、服务器监控、物品与配方查询、背包渲染、身份认证和多服务器路由。
- **可复用协议边界**：通信协议同时提供[中文文档](TerraNoneBridge通信文档.md)和[英文文档](TerraNoneBridge_Protocol.md)，方便审查、排错和二次扩展。
- **双语维护**：安装、配置、指令说明和协议文档均提供中文和英文版本。
- **社区基础设施定位**：项目主要服务于自托管游戏服务器的运营者和社区维护者，帮助其将游戏内服务接入外部群组管理工作流。

项目采用情况和发行数据以以上公开分发页面为准，而不在 README 中固定写死，便于数据保持最新并由第三方独立核验。

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>

在 NoneBot2 项目的根目录下打开命令行，运行：

```bash
nb plugin install nonebot-plugin-terralink
```

</details>

<details>
<summary>使用包管理器安装</summary>

在 NoneBot2 项目中运行：

```bash
pip install nonebot-plugin-terralink
```

</details>

## ⚙️ 配置

在 NoneBot 的 `.env` 或 `.env.prod` 文件中配置以下选项：

```env
# 插件总开关
terralink_enabled=true

# WebSocket 监听端口（tModLoader 端连接此端口）
terralink_port=7778

# QQ 群内使用的指令前缀
terralink_cmd_prefix=/

# 资源路径（必选，用于加载本地纹理）
# 资源只能通过在游戏客户端安装 TerraNoneBridge 模组导出。
# 请先配置模组中的“自定义导出路径”，创建一个空的导出目录，
# 然后在单人模式或本地主机模式下运行 "/tnb exportassets"。
# 最后将导出的资源放到 Bot 服务器可访问的位置。
# 示例："/www/program/nonebot2/lolbot/data/terralink/tmodass"
#       "data/terralink/tmodass"
terralink_resource_path=""

# 群管理开关的持久化文件路径，留空时使用
# data/terralink/group_settings.json
terralink_state_path=""

# 多服务器映射列表（JSON 格式）
terralink_links=[
    {"token": "your_secret_token_1", "group_id": 123456789, "name": "生存服"},
    {"token": "your_secret_token_2", "group_id": 987654321, "name": "灾厄服"}
]
```

---

## 💻 指令列表

### 0. 群管理指令（SuperUser / 群主 / 群管理员可用）

用于按群控制 TerraLink 的转发行为，设置会持久化保存。所有开关默认开启，以兼容旧版本行为。

- **查看状态**：`/terralink status`
- **开关事件播报**：`/terralink event <on/off>`
- **开关双向群服互通**：`/terralink bridge <on/off>`
- **仅开关群到服聊天**：`/terralink group <on/off>`
- **仅开关服到群聊天**：`/terralink server <on/off>`
- **重置本群设置**：`/terralink reset`
- **别名**：`tl`、`群服管理`

### 1. 管理指令（仅 SuperUser 可用）

#### 💀 `boss`
查看当前世界的 Boss 击杀进度。
- **指令**：`/boss`
- **别名**：`bosses`、`进度`

![boss 效果图](/imgs/boss.png)

#### 💊 `buff`
给予指定玩家或全体玩家 Buff。
- **指令**：`/buff <玩家/all> <Buff名> [秒数]`

![buff 效果图](/imgs/buff.png)

#### 🗡️ `butcher`
清理服务器内所有敌对生物。
- **指令**：`/butcher`

![butcher 效果图](/imgs/butcher.png)

#### 📤 `exportassets`
导出游戏内纹理等资源。该操作较耗时，Bot 端会拦截此指令以防误触。
- **指令**：`/export` 或 `/exportassets`

#### 🎁 `give`
给予指定玩家物品。
- **指令**：`/give <玩家> <物品名> [数量]`

![give 效果图](/imgs/give.png)

#### 🦵 `kick`
踢出指定玩家。
- **指令**：`/kick <玩家名> [原因]`

![kick 效果图](/imgs/kick.png)

#### 💾 `save`
强制保存世界存档。
- **指令**：`/save`

![save 效果图](/imgs/save.png)

#### 💧 `settle`
强制沉降世界内的所有液体。
- **指令**：`/settle`

![settle 效果图](/imgs/settle.png)

#### ⏰ `time`
查询或修改世界时间。
- **指令**：`/time [dawn/noon/dusk/midnight]`
- **说明**：不带参数时查询时间，带参数时设置时间。

![time 效果图](/imgs/time.png)

---

### 2. 查询指令（所有用户可用）

#### 📖 `help`
显示指令帮助菜单。
- **指令**：`/help`
- **别名**：`帮助`、`菜单`

![help 效果图](/imgs/help.png)

#### 🎒 `inv`
查看指定玩家的背包、装备和饰品栏。
- **指令**：`/inv <玩家名>`
- **别名**：`inventory`、`查背包`

![inv 效果图](/imgs/inv.png)

#### 👥 `list`
查看当前在线玩家列表。
- **指令**：`/list`
- **别名**：`在线`、`who`、`ls`

![list 效果图](/imgs/list.png)

#### 🔍 `query`
查询物品详细信息，包括属性、掉落、NPC 售卖和简易合成。
- **指令**：`/query <物品名或ID>`
- **别名**：`查询`、`属性`

![query 效果图](/imgs/query.png)

#### 🔨 `recipe`
生成物品的完整合成树图片，包含所有前置材料。
- **指令**：`/recipe <物品名或ID>`
- **别名**：`合成`、`配方`

![recipe 效果图](/imgs/recipe.png)

#### 🔎 `search`
模糊搜索物品名称。
- **指令**：`/search <关键词>`
- **别名**：`搜索`、`查找`

![search 效果图](/imgs/search.png)

#### 📊 `tps`
查看服务器性能状态，包括 TPS、内存和实体数量等信息。
- **指令**：`/tps`
- **别名**：`status`、`性能`

![tps 效果图](/imgs/tps.png)

---

## 📄 许可证

Copyright © 2026 newcovid。

本项目仅依据 [GNU General Public License v3.0](LICENSE)（`GPL-3.0-only`）发布。
