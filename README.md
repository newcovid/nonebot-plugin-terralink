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

**TerraLink** 是一个 NoneBot2 插件，用于实现泰拉瑞亚 TModLoader 服务器与 QQ 群的双向互通。通过 WebSocket 协议连接 TML 模组客户端，将游戏内的聊天消息、事件通知同步到 QQ 群，同时支持从 QQ 群发送指令到游戏服务器进行管理操作。

### 核心特性

- 🔗 **双向通信**：游戏消息 ↔ QQ 群消息实时同步
- 🎮 **完整的指令系统**：支持 15+ 个服务器管理和查询指令
- 🔐 **安全的认证机制**：Token-based 鉴权系统
- 📱 **多服务器支持**：一个 Bot 可同时管理多个 TML 服务器，绑定到不同的 QQ 群
- ⚙️ **灵活的配置**：支持自定义端口、指令前缀、多服务器映射
- 🚀 **高效的异步架构**：基于 asyncio 和 websockets 的高性能实现

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

<details>
<summary>pdm</summary>

```bash
pdm add nonebot-plugin-terralink
```

</details>

<details>
<summary>poetry</summary>

```bash
poetry add nonebot-plugin-terralink
```

</details>

<details>
<summary>conda</summary>

```bash
conda install nonebot-plugin-terralink
```

</details>

</details>

## ⚙️ 配置

在 NoneBot 的 `.env` 或 `.env.prod` 文件中配置以下选项：

```env
# 插件总开关
terralink_enabled=true

# WebSocket 监听端口
terralink_port=7778

# 指令前缀 (用于识别指令消息)
terralink_cmd_prefix=/

# 多服务器映射列表 (JSON 格式)
terralink_links=[
    {"token": "server_survival", "group_id": 11111, "name": "生存服"},
    {"token": "server_calamity", "group_id": 22222, "name": "灾厄服"}
]
```

### 配置说明

| 配置项                 | 类型             | 默认值 | 说明                   |
| ---------------------- | ---------------- | ------ | ---------------------- |
| `terralink_enabled`    | bool             | `true` | 插件是否启用           |
| `terralink_port`       | int              | `7778` | WebSocket 服务监听端口 |
| `terralink_cmd_prefix` | str              | `/`    | 指令前缀符号           |
| `terralink_links`      | List[LinkConfig] | `[]`   | 服务器配置列表         |

### LinkConfig (服务器配置)

```python
{
    "token": str,      # TML 端配置的 AccessToken (作为唯一识别码)
    "group_id": int,   # 绑定的 QQ 群号
    "name": str        # 服务器名称 (用于日志和消息前缀)
}
```

## 🎮 使用指南

### 游戏方（TML 服务器）配置

1. 在 TML 服务器中安装 **TerraNoneBridge** 模组
2. 在模组配置中设置：
   - 服务器地址：Bot 所在服务器的 IP 地址
   - 端口号：与 `terralink_port` 配置一致（默认 7778）
   - AccessToken：与 `terralink_links` 中对应的 token 一致

### QQ 群管理指令

#### 超级用户指令（管理指令）

只有超级用户 (SuperUser) 可以执行以下指令：

| 指令       | 用法                               | 功能             |
| ---------- | ---------------------------------- | ---------------- |
| `/kick`    | `/kick <玩家名> [原因]`            | 踢出玩家         |
| `/butcher` | `/butcher`                         | 清理所有敌对生物 |
| `/give`    | `/give <玩家> <物品名> [数量]`     | 给予玩家物品     |
| `/buff`    | `/buff <玩家/all> <Buff名> [秒数]` | 给玩家添加 Buff  |
| `/save`    | `/save`                            | 强制保存世界存档 |
| `/settle`  | `/settle`                          | 强制沉降所有液体 |
| `/time`    | `/time <dawn/noon/dusk/midnight>`  | 修改世界时间     |
| `/cmd`     | `/cmd <指令> [参数]`               | 原生指令透传     |

#### 普通用户指令（查询指令）

所有群成员都可以执行以下指令：

| 指令      | 别名              | 用法                 | 功能                 |
| --------- | ----------------- | -------------------- | -------------------- |
| `/help`   | 帮助, 菜单        | `/help`              | 查看指令列表         |
| `/list`   | 在线, who, ls     | `/list`              | 查看在线玩家列表     |
| `/tps`    | status, 性能      | `/tps`               | 查看服务器性能数据   |
| `/boss`   | bosses, 进度      | `/boss`              | 查看已击败 Boss 列表 |
| `/inv`    | inventory, 查背包 | `/inv <玩家名>`      | 查看玩家背包         |
| `/search` | 搜索, 查找        | `/search <关键词>`   | 搜索物品             |
| `/query`  | 查询, 合成        | `/query <物品名/ID>` | 查询物品属性和合成表 |

### 聊天同步

- 玩家在游戏内发送的聊天消息会自动转发到绑定的 QQ 群
- QQ 群内的文本消息会转发到游戏内（格式：`<昵称> 消息内容`）
- 指令消息（以 `/`、`#`、`.` 开头）不会被转发

## 🔌 协议细节

### WebSocket 连接流程

1. **建立连接**：TML 客户端连接到 `ws://<bot-ip>:<port>`

2. **鉴权阶段**：
   ```json
   // 客户端 -> 服务器
   {
     "type": "auth",
     "token": "server_survival",
     "timestamp": 1678888888
   }
   
   // 服务器 -> 客户端 (成功)
   {
     "type": "auth_response",
     "success": true,
     "message": "Authentication Successful!",
     "timestamp": 1678888890
   }
   ```

3. **数据交换**：鉴权成功后即可进行双向数据传输

### 数据包格式

#### 聊天消息 (Chat)

```json
{
  "type": "chat",
  "user_name": "玩家名/System",
  "message": "消息内容",
  "color": "FFFFFF",
  "timestamp": 1678888888
}
```

#### 系统事件 (Event)

```json
{
  "type": "event",
  "event_type": "boss_spawn",
  "world_name": "My World",
  "motd": "Boss Eye of Cthulhu has appeared!",
  "timestamp": 1678889000
}
```

支持的事件类型：
- `server_ready` - 连接就绪
- `world_load` - 世界加载完成
- `world_unload` - 世界卸载/服务器关闭
- `boss_spawn` - Boss 生成
- `boss_kill` - Boss 被击败

#### 执行指令 (Command)

```json
{
  "type": "command",
  "command": "give",
  "args": ["PlayerName", "Zenith", "1"],
  "timestamp": 1678888888
}
```

## 📂 项目结构

```
nonebot_plugin_terralink/
├── __init__.py                 # 插件入口和元数据
├── config.py                   # 配置模型定义
├── core/
│   ├── connection.py          # WebSocket 连接管理
│   ├── models.py              # 数据包模型
│   └── server.py              # WebSocket 服务器
├── matchers/
│   ├── admin.py               # 超级用户管理指令
│   ├── chat.py                # 聊天转发处理
│   └── query.py               # 查询指令处理
└── services/
    └── bridge.py              # 业务逻辑层（消息转发和处理）
```

## 🔧 架构设计

### 核心模块

- **Server** (`core/server.py`)：WebSocket 服务器，处理 TML 客户端连接和断开
- **Connection** (`core/connection.py`)：连接会话管理，维护 TML 连接状态和群绑定关系
- **Models** (`core/models.py`)：数据包的 Pydantic 模型定义
- **Bridge** (`services/bridge.py`)：业务逻辑层，处理数据包转发和 QQ 消息发送

### 关键特性

1. **多服务器支持**：通过 Token-based 认证和 Group-based 映射实现多服务器同时管理
2. **会话管理**：SessionManager 维护所有 TML 连接的状态和群绑定信息
3. **异步架构**：使用 asyncio 和 websockets 实现高效的并发处理
4. **错误恢复**：自动处理连接异常，提供重连机制

## ⚠️ 注意事项

1. **网络配置**：确保 Bot 运行的主机和 TML 服务器之间网络通畅
2. **防火墙配置**：需要开放 WebSocket 端口（默认 7778）
3. **Token 安全**：不要泄露 AccessToken，建议在生产环境中使用强随机 Token
4. **群号配置**：确保 `group_id` 与实际 QQ 群号一致
5. **鉴权机制**：TML 客户端必须先发送鉴权请求，否则其他消息会被丢弃

## 🐛 故障排除

### 常见问题

**Q: 连接后无法收到游戏消息**
- A: 检查 TML 端配置的 Token 是否与 `terralink_links` 中的 token 一致
- 检查网络连接是否畅通
- 查看 NoneBot 日志是否有错误信息

**Q: 指令发送后没有回显**
- A: 确认当前群已绑定服务器且服务器连接状态正常
- 检查是否有相应的权限（部分指令需要超级用户权限）
- 查看 TML 服务器的日志

**Q: WebSocket 端口被占用**
- A: 修改 `terralink_port` 配置为其他未使用的端口
- 或关闭占用该端口的其他进程

**Q: 鉴权失败**
- A: 检查 Token 是否正确且未包含特殊字符
- 确认服务器配置中的 Token 与客户端发送的 Token 一致

## 📝 开发信息

### 依赖项

- `nonebot2 >= 2.3.0`
- `nonebot-adapter-onebot >= 2.3.0`
- `websockets >= 11.0`
- `pydantic >= 1.10.0`

### Python 版本要求

- Python >= 3.9

### 许可证

GPL-3.0

### 作者

- **newcovid** <280310454@qq.com>

### 项目链接

- GitHub: https://github.com/newcovid/nonebot-plugin-terralink
- PyPI: https://pypi.org/project/nonebot-plugin-terralink/

## 📚 相关文档

- [NoneBot2 官方文档](https://v2.nonebot.dev/)
- [OneBot 适配器文档](https://adapter.onebot.dev/)
- [WebSocket 协议详细说明](./TerraNoneBridge通信文档.md)

## 🎯 未来计划

- [ ] 支持更多的服务器查询功能
- [ ] 添加数据库支持以记录历史消息
- [ ] 实现玩家排行榜功能
- [ ] 增加消息过滤和关键词拦截功能
- [ ] Web 管理后台界面

## 💬 反馈与支持

如有任何问题或建议，欢迎通过以下方式联系：

- 在 GitHub 上提交 [Issue](https://github.com/newcovid/nonebot-plugin-terralink/issues)
- 提交 [Pull Request](https://github.com/newcovid/nonebot-plugin-terralink/pulls) 贡献代码

---

<div align="center">

Made with ❤️ by newcovid

</div>
