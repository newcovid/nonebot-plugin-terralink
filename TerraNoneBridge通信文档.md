# TerraLink (TerraNoneBridge) WebSocket 接口文档



本文档描述了 TerraNoneBridge 模组与外部客户端（如 Nonebot2 插件）之间的 WebSocket 通信协议。



## 1. 连接信息



* **协议**: WebSocket (ws://)

* **默认端口**: 7778 (可在 `ServerConfig` 中配置)

* **数据格式**: JSON

* **编码**: UTF-8



## 2. 基础数据结构



所有数据包均包含以下基础字段：



| 字段名 | 类型 | 说明 |

| :--- | :--- | :--- |

| `type` | `string` | 数据包类型 (Discriminator) |

| `timestamp` | `long` | UNIX 时间戳 (秒) |



## 3. 通信流程



### 3.1 鉴权流程 (握手)



连接建立后，**客户端必须发送的第一条消息是鉴权请求**。在鉴权成功前，服务端会丢弃所有其他类型的数据包。



#### [C -> S] 鉴权请求

* **Type**: `auth`



```json

{

  "type": "auth",

  "token": "你的AccessToken", 

  "timestamp": 1678888888

}

```



#### [S -> C] 鉴权响应

* **Type**: `auth_response`



```json

{

  "type": "auth_response",

  "success": true, // true 表示鉴权成功，false 表示失败

  "message": "Authentication Successful!", // 或错误原因

  "timestamp": 1678888890

}

```



> **注意**: 如果鉴权失败，服务端会在发送响应后立即断开连接。



## 4. 客户端发送 (Nonebot -> TML)



### 4.1 发送聊天消息

将 QQ 群消息转发到游戏内。



* **Type**: `chat`



```json

{

  "type": "chat",

  "user_name": "用户昵称",

  "message": "Hello Terraria!",

  "color": "00FF00", // (可选) 16进制颜色代码，不带#

  "timestamp": 1678888888

}

```



### 4.2 执行指令

远程执行模组提供的管理指令。



* **Type**: `command`



```json

{

  "type": "command",

  "command": "give", // 指令名 (不带 /)

  "args": ["PlayerName", "Zenith", "1"], // 参数列表

  "timestamp": 1678888888

}

```



## 5. 服务端推送 (TML -> Nonebot)



### 5.1 聊天消息与指令回显

包含游戏内玩家的聊天内容，以及**指令执行的结果回显**。



* **Type**: `chat`



| 字段 | 类型 | 说明 |

| :--- | :--- | :--- |

| `user_name` | `string` | 发送者名称。如果是指令回显或系统消息，通常为 "System" (系统) 或 "Server" (服务器) |

| `message` | `string` | 聊天内容或指令执行结果 |

| `color` | `string` | 消息颜色的 Hex 代码 |



```json

{

  "type": "chat",

  "user_name": "Player1",

  "message": "这Boss太难打了",

  "color": "FFFFFF",

  "timestamp": 1678888900

}

```



### 5.2 系统事件

服务器状态变更或游戏内重要事件。



* **Type**: `event`



| 字段 | 类型 | 说明 |

| :--- | :--- | :--- |

| `event_type` | `string` | 事件子类型 (见下表) |

| `world_name` | `string` | 当前世界名称 |

| `motd` | `string` | 事件描述文本 (已本地化) |



**事件类型 (`event_type`) 列表:**



| event_type | 触发时机 | Motd 示例 |

| :--- | :--- | :--- |

| `server_ready` | 鉴权成功且连接就绪时 | "Connection Established" |

| `world_load` | 世界加载完成时 | "Server Started" |

| `world_unload` | 世界卸载/服务器关闭时 | "Server Stopping" |

| `boss_spawn` | Boss 生成时 | "Boss King Slime has appeared!" |

| `boss_kill` | Boss 被击败时 | "Boss King Slime has been defeated!" |



```json

{

  "type": "event",

  "event_type": "boss_spawn",

  "world_name": "My World",

  "motd": "Boss Eye of Cthulhu has appeared!",

  "timestamp": 1678889000

}

```



## 6. 可用指令列表



Nonebot 插件可以通过发送 `command` 包来调用以下功能。



| 指令名 | 参数格式 | 功能描述 |

| :--- | :--- | :--- |

| `help` | N/A | 查看指令列表 |

| `list` | N/A | 查看在线玩家列表 |

| `tps` | N/A | 查看服务器 TPS、内存、实体数等性能数据 |

| `boss` | N/A | 查看当前世界已击败的 Boss 列表 |

| `time` | `<dawn/noon/dusk/midnight>` | 修改世界时间 |

| `settle` | N/A | 强制沉降所有液体 |

| `save` | N/A | 强制保存世界存档 |

| `kick` | `<player> [reason]` | 踢出指定玩家 |

| `butcher` | N/A | 清理所有敌对生物 (杀怪) |

| `give` | `<player> <item> [amount]` | 给予玩家物品 (支持模糊搜索) |

| `buff` | `<player/all> <buff> [sec]` | 给玩家添加 Buff (支持 ID 或名称) |

| `inv` | `<player>` | 查看玩家背包内容 (文本形式) |

| `search` | `<keyword>` | 搜索物品 ID 或 Buff ID |

| `query` | `<name/id>` | 查询物品详细属性和合成表 |