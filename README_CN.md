[English](README.md) | [通信协议](TerraNoneBridge通信文档.md)

<div align="center">

# nonebot-plugin-terralink

**面向 Terraria tModLoader 服务器的 NoneBot2 集成层**

[![License](https://img.shields.io/github/license/newcovid/nonebot-plugin-terralink.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/nonebot-plugin-terralink.svg)](https://pypi.org/project/nonebot-plugin-terralink/)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)

</div>

## 项目简介

**TerraLink** 通过一套明确的 WebSocket 协议，将 Terraria tModLoader 服务器接入基于 [NoneBot2](https://nonebot.dev/) 构建的机器人应用。项目把游戏服务器事件、运维操作、性能数据和游戏内容查询封装成可集成到现有自动化工作流中的 Bot 侧能力。

项目由本仓库中的 NoneBot2 插件和配套的 [`TerraNoneBridge`](https://steamcommunity.com/sharedfiles/filedetails/?id=3617766364) tModLoader 模组组成。两端通过带鉴权的协议通信，并可独立部署和升级。

### 核心能力

- **双向事件桥接**：在 tModLoader 服务器和指定 Bot 会话之间转发聊天及服务器事件。
- **服务器运维**：执行存档、玩家管理、时间调整、敌对实体清理等管理操作。
- **游戏数据查询**：查询物品、配方、背包、世界进度、在线玩家和服务器状态。
- **结构化渲染**：使用 HTML/CSS 将背包、物品信息、合成树和运维数据渲染为图片。
- **多服务器路由**：由一个 NoneBot2 实例同时管理多个 tModLoader 服务器。
- **鉴权通信**：通过独立 Token 隔离和认证不同服务器连接。
- **异步架构**：基于 `asyncio` 与 `websockets` 处理并发连接和事件推送。

## 架构与适配器支持

TerraLink 将 tModLoader 通信协议、连接管理、数据渲染和指令服务与 Bot 平台侧的消息处理逻辑分离。因此，在增加其他 NoneBot2 适配器支持时，可以复用现有核心模块，而不需要重新设计游戏服务器协议。

当前版本内置的是 **OneBot V11 群组传输层**，其中消息事件、群组标识和权限判断属于适配器特定实现。接入其他 NoneBot2 适配器时，只需实现对应的传输层，将该适配器的会话与权限模型映射到 TerraLink 的核心服务。

## 生态定位与使用场景

TerraLink 将通用机器人框架扩展为游戏服务器运维入口。服务器运营者可以把实时事件、远程管理、运行监控和游戏数据查询接入已有的 Bot 工作流，并与通知、审核、定时任务及社区管理能力组合使用。

通过把游戏服务器协议与 Bot 平台侧传输逻辑解耦，项目为后续扩展其他适配器、管理界面和自动化场景提供了稳定基础。Python 插件通过 [PyPI](https://pypi.org/project/nonebot-plugin-terralink/) 发布，配套模组通过 [Steam 创意工坊](https://steamcommunity.com/sharedfiles/filedetails/?id=3617766364) 分发。

## 安装

使用 `nb-cli`：

```bash
nb plugin install nonebot-plugin-terralink
```

使用 `pip`：

```bash
pip install nonebot-plugin-terralink
```

还需要在每个待接入的 tModLoader 服务器上安装并配置配套的 `TerraNoneBridge` 模组。

## 配置

在 NoneBot 的 `.env` 或 `.env.prod` 文件中加入以下选项：

```env
# 插件总开关
terralink_enabled=true

# TerraNoneBridge 连接使用的 WebSocket 监听端口
terralink_port=7778

# Bot 会话中使用的 TerraLink 指令前缀
terralink_cmd_prefix=/

# TerraNoneBridge 导出的本地纹理目录
# 在模组中配置自定义导出路径，并在单人或本地主机模式下运行
# "/tnb exportassets"。随后将导出的资源复制到 NoneBot2 进程可访问的位置。
terralink_resource_path="data/terralink/tmodass"

# 会话级桥接开关的持久化文件
# 留空时使用 data/terralink/group_settings.json
terralink_state_path=""

# 服务器与 Bot 会话的映射关系
# 当前 OneBot V11 传输层中，group_id 表示目标群组 ID。
terralink_links=[
    {"token": "your_secret_token_1", "group_id": 123456789, "name": "生存服"},
    {"token": "your_secret_token_2", "group_id": 987654321, "name": "灾厄服"}
]
```

每个 `token` 必须与对应 `TerraNoneBridge` 实例中的配置保持一致。

## 指令

### 桥接控制

在内置的 OneBot V11 传输层中，以下指令可由 SuperUser、群主和群管理员使用。设置会按绑定群组持久化保存。

- **查看状态**：`/terralink status`
- **开关事件转发**：`/terralink event <on/off>`
- **开关完整桥接**：`/terralink bridge <on/off>`
- **开关 Bot 到服务器聊天**：`/terralink group <on/off>`
- **开关服务器到 Bot 聊天**：`/terralink server <on/off>`
- **重置桥接设置**：`/terralink reset`
- **别名**：`tl`、`群服管理`

### 管理指令

管理指令需要 NoneBot SuperUser 权限。

#### `boss`

查看世界进度和已击败 Boss。

```text
/boss
```

![boss 效果图](/imgs/boss.png)

#### `buff`

为指定玩家或所有玩家添加 Buff。

```text
/buff <玩家/all> <Buff名> [秒数]
```

![buff 效果图](/imgs/buff.png)

#### `butcher`

清理服务器中的敌对实体。

```text
/butcher
```

![butcher 效果图](/imgs/butcher.png)

#### `exportassets`

请求导出游戏资源。由于该操作可能消耗较多时间，Bot 端会拦截意外的远程执行。

```text
/export
/exportassets
```

#### `give`

向玩家发放物品。

```text
/give <玩家> <物品名> [数量]
```

![give 效果图](/imgs/give.png)

#### `kick`

将玩家移出服务器。

```text
/kick <玩家名> [原因]
```

![kick 效果图](/imgs/kick.png)

#### `save`

强制保存当前世界。

```text
/save
```

![save 效果图](/imgs/save.png)

#### `settle`

强制沉降世界中的液体。

```text
/settle
```

![settle 效果图](/imgs/settle.png)

#### `time`

查询或调整世界时间。

```text
/time [dawn/noon/dusk/midnight]
```

![time 效果图](/imgs/time.png)

### 查询指令

#### `help`

显示指令菜单。

```text
/help
```

别名：`帮助`、`菜单`

![help 效果图](/imgs/help.png)

#### `inv`

渲染玩家的背包、装备和饰品信息。

```text
/inv <玩家名>
```

别名：`inventory`、`查背包`

![inv 效果图](/imgs/inv.png)

#### `list`

列出当前在线玩家。

```text
/list
```

别名：`在线`、`who`、`ls`

![list 效果图](/imgs/list.png)

#### `query`

查询物品属性、掉落、NPC 售卖和直接配方。

```text
/query <物品名或ID>
```

别名：`查询`、`属性`

![query 效果图](/imgs/query.png)

#### `recipe`

生成物品的完整合成树。

```text
/recipe <物品名或ID>
```

别名：`合成`、`配方`

![recipe 效果图](/imgs/recipe.png)

#### `search`

搜索物品名称。

```text
/search <关键词>
```

别名：`搜索`、`查找`

![search 效果图](/imgs/search.png)

#### `tps`

查看服务器性能、内存使用和实体数量。

```text
/tps
```

别名：`status`、`性能`

![tps 效果图](/imgs/tps.png)

## 通信协议

插件与 `TerraNoneBridge` 之间的通信约定见[通信协议文档](TerraNoneBridge通信文档.md)。

## 许可证

Copyright © 2026 newcovid。

本项目仅依据 [GNU General Public License v3.0](LICENSE)（`GPL-3.0-only`）发布。
