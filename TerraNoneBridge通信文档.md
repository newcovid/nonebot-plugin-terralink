[中文 README](README_CN.md) | [English README](README.md) | [中文通信文档](TerraNoneBridge通信文档.md) | [English Protocol](TerraNoneBridge_Protocol.md)

# TerraNoneBridge 通讯接口文档 (WebSocket / Nonebot2 适配版)

## 1. 概述

本稳定通过 WebSocket 协议实现泰拉瑞亚服务器 (tModLoader) 与 Nonebot2 机器人端的高效双向通讯。
服务端监听配置中指定的端口（默认 7778），客户端（Nonebot）需主动发起连接。

### 核心机制
* **通讯协议**: WebSocket
* **数据格式**: JSON
* **鉴权机制**: 基于 Token 的握手验证
* **并发控制**: 使用 `id` 字段追踪异步请求与响应 (类似 JSON-RPC)

---

## 2. 基础协议结构

所有数据包均继承自基础包结构。`type` 字段决定了数据包的具体用途。

```json
{
  "type": "具体的包类型 (auth / auth_response / event / chat / command / command_response)",
  "timestamp": 1715000000
}
```

---

## 3. 连接与鉴权

连接建立后，客户端必须在 10 秒内发送鉴权包，否则连接将被断开。

### 3.1 发送鉴权请求 (Client -> Server)

* **type**: `auth`
* **token**: 配置文件 `ServerConfig.cs` 中的 `AccessToken`。

**示例:**
```json
{
  "type": "auth",
  "token": "my_secure_access_token_123456",
  "timestamp": 1715000100
}
```

### 3.2 鉴权响应 (Server -> Client)

* **type**: `auth_response`
* **success**: 布尔值，标识鉴权是否通过。
* **message**: 状态描述。

**示例:**
```json
{
  "type": "auth_response",
  "success": true,
  "message": "Authentication successful.",
  "timestamp": 1715000101
}
```

---

## 4. 事件广播 (Server -> Client)

服务端主动推送的消息，无需请求 ID。

### 4.1 聊天消息同步 (`chat`)
当游戏内玩家发送消息，或服务器广播系统消息 (Boss、入侵、死亡等) 时触发。

**数据结构:**
* **user_name**: 发送者名称 (系统消息通常为 "Server")
* **message**: 消息内容。物品 (`[i:...]`)、颜色 (`[c/...:...]`) 等聊天标签已转换为可读文本，例如 `[传奇 天顶剑]`。
* **color**: 消息颜色的 16 进制代码
* **category**: 消息分类 (模组 0.9.0 起提供，旧版本不携带)

| category | 说明 |
| --- | --- |
| `chat` | 玩家聊天 |
| `join_leave` | 玩家加入/离开 |
| `death` | 玩家死亡 |
| `boss` | Boss 苏醒/被打败及 Boss 预警 |
| `event` | 入侵、天象、世界进度、传送等原版事件 |
| `npc` | 城镇 NPC 到达/死亡/离开 |
| `mod` | 其他模组发出的播报 |
| `server` | 控制台 `say` 消息 |

在模组配置中被关闭的消息 (`EnableChatSync`、`EnableEventBroadcast`、`Broadcast*`、`BlockedKeywords`) 不会发送。

**示例:**
```json
{
  "type": "chat",
  "user_name": "TerrarianPlayer",
  "message": "Hello from Terraria!",
  "color": "32FF82",
  "category": "chat",
  "timestamp": 1715000200
}
```

### 4.2 服务器事件 (`event`)
涵盖世界加载、Boss生成/击杀等。

**数据结构:**
* **event_type**: 事件子类型 (`world_load`, `world_unload`, `server_ready`, `boss_spawn`, `boss_kill`)
* **world_name**: 世界名称
* **motd**: 事件描述文本

**示例:**
```json
{
  "type": "event",
  "event_type": "boss_spawn",
  "world_name": "MyExpertWorld",
  "motd": "Eye of Cthulhu has awoken!",
  "timestamp": 1715000300
}
```

---

## 5. 指令交互系统

客户端发送 `command` 包，服务端处理后返回 `command_response` 包。

### 5.1 请求格式 (Client -> Server)

**字段说明:**
* **type**: 固定为 `command`
* **command**: 指令名称 (不带前缀，如 `list`)
* **args**: 参数列表
* **id**: **[关键]** 请求唯一标识符 (UUID 或随机字符串)，用于将响应对应回请求。

**通用请求示例:**
```json
{
  "type": "command",
  "command": "give",
  "args": ["PlayerName", "Zenith", "1"],
  "id": "req-uuid-550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1715000400
}
```

### 5.2 响应格式 (Server -> Client)

**字段说明:**
* **type**: 固定为 `command_response`
* **status**: `success` 或 `error`
* **message**: 人类可读的返回消息 (用于直接展示)
* **data**: 结构化的数据对象 (用于程序处理，不同指令结构不同)
* **id**: 回传请求中的 `id`

**通用响应示例:**
```json
{
  "type": "command_response",
  "status": "success",
  "message": "Given Zenith x1 to PlayerName.",
  "data": { ... }, 
  "id": "req-uuid-550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1715000401
}
```

---

## 6. 具体指令详解 (Command Detail)

以下所有响应均位于 `command_response` 包的 `data` 字段中。
**注意**: 所有示例数据均保证非空且包含完整字段。

### 6.1 `list` - 查询在线玩家
* **说明**: 获取当前服务器在线玩家列表。
* **Args**: 无

**Response Data 示例:**
```json
{
  "count": 2,
  "max": 16,
  "players": [
    "Alice",
    "Bob"
  ]
}
```

### 6.2 `tps` - 服务器性能状态
* **说明**: 获取 TPS、内存占用及实体统计。
* **Args**: 无

**Response Data 示例:**
```json
{
  "version": "v2024.05.3.1",
  "world": "BuildersWorkshop",
  "tps": 59.9,
  "onlineCount": 5,
  "npcCount": 120,
  "itemCount": 45,
  "memoryMb": 2048,
  "gcMb": 150
}
```

### 6.3 `time` - 时间管理
* **说明**: 查询或设置世界时间。
* **Args**: 
    * 查询: 无 或 `[]`
    * 设置: `["set", "morning" / "noon" / "evening" / "midnight" / "18000"]`

**Response Data 示例:**
```json
{
  "timeString": "04:30",
  "isDay": true,
  "moonPhase": "Full Moon",
  "moonPhaseId": 0,
  "rawTime": 0.0,
  "action": "query" 
}
```
*(注: 若 action 为 "set"，数据结构相同，仅数值变化)*

### 6.4 `boss` - Boss 击杀进度
* **说明**: 获取当前世界的 Boss 击杀清单（包含模组 Boss）。
* **Args**: 无

**Response Data 示例:**
```json
{
  "worldName": "TerraWorld",
  "difficulty": "Master",
  "defeated": [
    {
      "name": "King Slime",
      "isDowned": true,
      "type": "Vanilla"
    },
    {
      "name": "Eye of Cthulhu",
      "isDowned": true,
      "type": "Vanilla"
    }
  ],
  "undefeated": [
    {
      "name": "Moon Lord",
      "isDowned": false,
      "type": "Vanilla"
    },
    {
      "name": "Supreme Calamitas",
      "isDowned": false,
      "type": "Mod/Checklist"
    }
  ]
}
```

### 6.5 `inv` - 查看玩家背包
* **说明**: 查询指定玩家的背包、装备及饰品数据。
* **Args**: `["<PlayerName>"]`

**Response Data 示例:**
```json
{
  "playerName": "Alice",
  "inventory": [
    {
      "slot": 0,
      "id": 757,
      "name": "Terra Blade",
      "stack": 1,
      "prefix": "Legendary",
      "imagePath": "Item/TerraBlade.png",
      "frameCount": 1
    },
    {
      "slot": 1,
      "id": 29,
      "name": "Life Crystal",
      "stack": 5,
      "prefix": "",
      "imagePath": "Item/LifeCrystal.png",
      "frameCount": 1
    }
  ],
  "armor": [
    {
      "slot": 0,
      "id": 123,
      "name": "Solar Flare Helmet",
      "stack": 1,
      "prefix": "",
      "imagePath": "Item/SolarFlareHelmet.png",
      "frameCount": 1
    },
    {
      "slot": 1,
      "id": 124,
      "name": "Solar Flare Breastplate",
      "stack": 1,
      "prefix": "",
      "imagePath": "Item/SolarFlareBreastplate.png",
      "frameCount": 1
    }
  ],
  "misc": [
    {
      "slot": 0,
      "id": 497,
      "name": "Neptune's Shell",
      "stack": 1,
      "prefix": "Warding",
      "imagePath": "Item/NeptunesShell.png",
      "frameCount": 1
    },
    {
      "slot": 100,
      "id": 1000,
      "name": "Red Dye",
      "stack": 3,
      "prefix": "",
      "imagePath": "Item/RedDye.png",
      "frameCount": 1
    }
  ]
}
```

### 6.6 `query` - 查询物品详情
* **说明**: 获取物品详细属性、掉落源、出售NPC及合成表概览。
* **Args**: `["<ItemName>" / "<ItemID>"]`

**Response Data 示例:**
```json
{
  "id": 757,
  "name": "Terra Blade",
  "mod": "Terraria",
  "type": "Item",
  "imagePath": "Item/TerraBlade.png",
  "frameCount": 1,
  "stats": {
    "damage": 115,
    "defense": 0,
    "crit": 4,
    "useTime": 14,
    "knockBack": 6.5,
    "value": 200000,
    "autoReuse": true,
    "consumable": false,
    "maxStack": 1
  },
  "description": "Fires a green projectile",
  "droppedBy": [
    {
      "name": "Mothron",
      "imagePath": "Npc/Mothron.png"
    },
    {
      "name": "Reaper",
      "imagePath": "Npc/Reaper.png"
    }
  ],
  "soldBy": [
    {
      "name": "Cyborg",
      "imagePath": "Npc/Cyborg.png"
    },
    {
      "name": "Goblin Tinkerer",
      "imagePath": "Npc/GoblinTinkerer.png"
    }
  ],
  "recipes": [
    {
      "resultName": "Terra Blade",
      "resultCount": 1,
      "stations": [
        {
          "name": "Mythril Anvil",
          "stack": 1,
          "id": 525,
          "imagePath": "Item/MythrilAnvil.png",
          "frameCount": 1
        }
      ],
      "ingredients": [
        {
          "name": "True Night's Edge",
          "stack": 1,
          "id": 675,
          "imagePath": "Item/TrueNightsEdge.png",
          "frameCount": 1
        },
        {
          "name": "True Excalibur",
          "stack": 1,
          "id": 674,
          "imagePath": "Item/TrueExcalibur.png",
          "frameCount": 1
        }
      ]
    },
    {
      "resultName": "Terra Blade",
      "resultCount": 1,
      "stations": [],
      "ingredients": [] 
    }
  ]
}
```

### 6.7 `search` - 搜索物品
* **说明**: 模糊搜索物品，返回匹配列表。
* **Args**: `["<Keyword>"]`

**Response Data 示例:**
```json
{
  "query": "terra",
  "count": 5,
  "results": [
    {
      "id": 757,
      "name": "Terra Blade",
      "modName": "Terraria",
      "matchQuality": 1,
      "imagePath": "Item/TerraBlade.png",
      "frameCount": 1
    },
    {
      "id": 4976,
      "name": "Terraprisma",
      "modName": "Terraria",
      "matchQuality": 1,
      "imagePath": "Item/Terraprisma.png",
      "frameCount": 1
    }
  ]
}
```

### 6.8 `recipe` - 合成表查询 (复杂)
* **说明**: 递归查询合成树，包含目标物品的合成方式 (`craftRecipes`) 和用途 (`usageRecipes`)，以及所有相关物品的元数据 (`nodes`)。
* **Args**: `["<ItemName>" / "<ItemID>"]`

**Response Data 示例:**
```json
{
  "targetId": 8,
  "nodes": {
    "8": {
      "id": 8,
      "name": "Torch",
      "imagePath": "Item/Torch.png",
      "mod": "Terraria",
      "frameCount": 1
    },
    "9": {
      "id": 9,
      "name": "Wood",
      "imagePath": "Item/Wood.png",
      "mod": "Terraria",
      "frameCount": 1
    },
    "23": {
      "id": 23,
      "name": "Gel",
      "imagePath": "Item/Gel.png",
      "mod": "Terraria",
      "frameCount": 1
    }
  },
  "craftRecipes": [
    {
      "recipeId": 12345678,
      "resultId": 8,
      "resultCount": 3,
      "stations": [
        {
          "tileId": -1,
          "name": "Hand",
          "imagePath": ""
        }
      ],
      "conditions": [
        "Near Water"
      ],
      "ingredients": [
        {
          "itemId": 23,
          "count": 1,
          "groupName": null,
          "groupIds": null
        },
        {
          "itemId": 9,
          "count": 1,
          "groupName": "Any Wood",
          "groupIds": [9, 619, 620]
        }
      ]
    },
    {
       "recipeId": 87654321,
       "resultId": 8,
       "resultCount": 1,
       "stations": [],
       "conditions": [],
       "ingredients": []
    }
  ],
  "usageRecipes": [
    {
      "recipeId": 5555555,
      "resultId": 3001,
      "resultCount": 1,
      "stations": [],
      "conditions": [],
      "ingredients": [
         {
          "itemId": 8,
          "count": 99,
          "groupName": null,
          "groupIds": null
        }
      ]
    },
    {
       "recipeId": 444444,
       "resultId": 3002,
       "resultCount": 1,
       "stations": [],
       "conditions": [],
       "ingredients": []
    }
  ]
}
```

### 6.9 `give` - 给予物品
* **说明**: 给予玩家物品。需管理员权限。
* **Args**: `["<PlayerName>", "<ItemName>", "<Amount>"]`

**Response Data 示例:**
```json
{
  "player": "Alice",
  "item": "Zenith",
  "itemId": 4956,
  "amount": 1
}
```

### 6.10 `buff` - 给予Buff
* **说明**: 给予玩家或所有人Buff。需管理员权限。
* **Args**: `["<PlayerName> / all", "<BuffName/ID>", "<Seconds>"]`

**Response Data 示例:**
```json
{
  "targets": [
    "Alice",
    "Bob"
  ],
  "buff": "Ironskin",
  "duration": 3600
}
```

### 6.11 `kick` - 踢出玩家
* **说明**: 踢出指定玩家。需管理员权限。
* **Args**: `["<PlayerName>", "<Reason>"]`

**Response Data 示例:**
```json
{
  "target": "Griefer123",
  "reason": "Breaking rules",
  "success": true
}
```

### 6.12 `butcher` - 清理生物
* **说明**: 杀死所有非友善 NPC。需管理员权限。
* **Args**: 无

**Response Data 示例:**
```json
{
  "killedCount": 42
}
```

### 6.13 `save` - 保存世界
* **说明**: 触发世界保存。需管理员权限。
* **Args**: 无

**Response Data 示例:**
```json
{
  "success": true,
  "timestamp": 1715001000
}
```

### 6.14 `settle` - 液体沉降
* **说明**: 强制处理液体流动。需管理员权限。
* **Args**: 无

**Response Data 示例:**
```json
{
  "success": true
}
```

### 6.15 `help` - 获取指令帮助
* **说明**: 获取指令列表或特定指令用法。
* **Args**: 无 或 `["<CommandName>"]`

**Response Data 示例 (List):**
```json
[
  {
    "name": "list",
    "usage": "list",
    "description": "Show online players",
    "permission": "User"
  },
  {
    "name": "kick",
    "usage": "kick <player> [reason]",
    "description": "Kick a player",
    "permission": "Admin"
  }
]
```

### 6.16 `exportassets` - 资源导出
* **说明**: 导出游戏纹理资源（物品/NPC/Buff等）到本地。这是一个**长耗时**操作。
* **Args**: `["all"]` (可选，导出所有资源，否则仅导出 Core 类别)
* **特殊行为**: 该指令不同于其他指令，它会使用相同的 Request ID 发送**多个** `command_response` 包来更新进度。

**Response Data 流 (Stream):**

**Packet 1 (开始):**
```json
{
  "type": "command_response",
  "message": "Start exporting 5000 assets to ...",
  "data": null,
  "id": "req-id-1"
}
```

**Packet 2...N (进度更新):**
```json
{
  "type": "command_response",
  "message": "Exporting... 25% (1250/5000)",
  "data": null,
  "id": "req-id-1"
}
```

**Packet Final (完成):**
```json
{
  "type": "command_response",
  "message": "Export complete! Processed 5000 assets.",
  "data": null,
  "id": "req-id-1"
}
```