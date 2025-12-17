[中文 README](README_CN.md) | [English README](README.md) | [中文通信文档](TerraNoneBridge通信文档.md) | [English Protocol](TerraNoneBridge_Protocol.md)

# TerraNoneBridge Communication Interface Documentation (WebSocket / Nonebot2 Adapter)

## 1. Overview

This document outlines the high-efficiency two-way communication between the Terraria Server (tModLoader) and the Nonebot2 robot client using the WebSocket protocol.
The server listens on a configured port (default 7778), and the client (Nonebot) must actively initiate the connection.

### Core Mechanisms
* **Protocol**: WebSocket
* **Data Format**: JSON
* **Authentication**: Token-based handshake
* **Concurrency**: Uses `id` fields to track asynchronous requests and responses (similar to JSON-RPC)

---

## 2. Basic Protocol Structure

All data packets inherit from a base structure. The `type` field determines the specific purpose of the packet.

```json
{
  "type": "packet_type (auth / auth_response / event / chat / command / command_response)",
  "timestamp": 1715000000
}
```

---

## 3. Connection and Authentication

After the connection is established, the client must send an authentication packet within 10 seconds, otherwise the connection will be disconnected.

### 3.1 Authentication Request (Client -> Server)

* **type**: `auth`
* **token**: The `AccessToken` configured in `ServerConfig.cs`.

**Example:**
```json
{
  "type": "auth",
  "token": "my_secure_access_token_123456",
  "timestamp": 1715000100
}
```

### 3.2 Authentication Response (Server -> Client)

* **type**: `auth_response`
* **success**: Boolean, indicating if authentication passed.
* **message**: Status description.

**Example:**
```json
{
  "type": "auth_response",
  "success": true,
  "message": "Authentication successful.",
  "timestamp": 1715000101
}
```

---

## 4. Event Broadcasting (Server -> Client)

Messages proactively pushed by the server, no request ID required.

### 4.1 Chat Sync (`chat`)
Triggered when an in-game player sends a message.

**Data Structure:**
* **user_name**: Sender name (System messages are usually "Server")
* **message**: Message content
* **color**: Hex code of the message color

**Example:**
```json
{
  "type": "chat",
  "user_name": "TerrarianPlayer",
  "message": "Hello from Terraria!",
  "color": "32FF82",
  "timestamp": 1715000200
}
```

### 4.2 Server Events (`event`)
Covers world loading, Boss spawning/killing, etc.

**Data Structure:**
* **event_type**: Event subtype (`world_load`, `world_unload`, `server_ready`, `boss_spawn`, `boss_kill`)
* **world_name**: World name
* **motd**: Event description text

**Example:**
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

## 5. Command Interaction System

The client sends a `command` packet, and the server processes it and returns a `command_response` packet.

### 5.1 Request Format (Client -> Server)

**Fields:**
* **type**: Fixed as `command`
* **command**: Command name (without prefix, e.g., `list`)
* **args**: List of arguments
* **id**: **[Critical]** Unique Request Identifier (UUID or random string), used to map responses back to requests.

**Generic Request Example:**
```json
{
  "type": "command",
  "command": "give",
  "args": ["PlayerName", "Zenith", "1"],
  "id": "req-uuid-550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1715000400
}
```

### 5.2 Response Format (Server -> Client)

**Fields:**
* **type**: Fixed as `command_response`
* **status**: `success` or `error`
* **message**: Human-readable return message (for direct display)
* **data**: Structured data object (for programmatic processing, differs by command)
* **id**: The `id` from the originating request

**Generic Response Example:**
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

## 6. Command Details

All responses below are located in the `data` field of the `command_response` packet.
**Note**: All example data guarantees non-empty and complete fields.

### 6.1 `list` - Online Players
* **Desc**: Get the list of players currently online.
* **Args**: None

**Response Data Example:**
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

### 6.2 `tps` - Server Performance
* **Desc**: Get TPS, memory usage, and entity statistics.
* **Args**: None

**Response Data Example:**
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

### 6.3 `time` - Time Management
* **Desc**: Query or set world time.
* **Args**: 
    * Query: None or `[]`
    * Set: `["set", "morning" / "noon" / "evening" / "midnight" / "18000"]`

**Response Data Example:**
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
*(Note: If action is "set", data structure is same, only values change)*

### 6.4 `boss` - Boss Progression
* **Desc**: Get the list of defeated/undefeated bosses in the current world (supports modded bosses).
* **Args**: None

**Response Data Example:**
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

### 6.5 `inv` - Player Inventory
* **Desc**: Query specific player's inventory, armor, and accessories.
* **Args**: `["<PlayerName>"]`

**Response Data Example:**
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

### 6.6 `query` - Item Details
* **Desc**: Get item stats, drop sources, NPC sales, and recipe overview.
* **Args**: `["<ItemName>" / "<ItemID>"]`

**Response Data Example:**
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

### 6.7 `search` - Search Items
* **Desc**: Fuzzy search for items, returns a matching list.
* **Args**: `["<Keyword>"]`

**Response Data Example:**
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

### 6.8 `recipe` - Recipe Tree (Complex)
* **Desc**: Recursively queries the crafting tree, including how to craft the target item (`craftRecipes`), its usages (`usageRecipes`), and metadata for all referenced items (`nodes`).
* **Args**: `["<ItemName>" / "<ItemID>"]`

**Response Data Example:**
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

### 6.9 `give` - Give Item
* **Desc**: Give item to player. Requires Admin.
* **Args**: `["<PlayerName>", "<ItemName>", "<Amount>"]`

**Response Data Example:**
```json
{
  "player": "Alice",
  "item": "Zenith",
  "itemId": 4956,
  "amount": 1
}
```

### 6.10 `buff` - Give Buff
* **Desc**: Give buff to player or everyone. Requires Admin.
* **Args**: `["<PlayerName> / all", "<BuffName/ID>", "<Seconds>"]`

**Response Data Example:**
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

### 6.11 `kick` - Kick Player
* **Desc**: Kick specific player. Requires Admin.
* **Args**: `["<PlayerName>", "<Reason>"]`

**Response Data Example:**
```json
{
  "target": "Griefer123",
  "reason": "Breaking rules",
  "success": true
}
```

### 6.12 `butcher` - Kill Mobs
* **Desc**: Kill all hostile NPCs. Requires Admin.
* **Args**: None

**Response Data Example:**
```json
{
  "killedCount": 42
}
```

### 6.13 `save` - Save World
* **Desc**: Trigger world save. Requires Admin.
* **Args**: None

**Response Data Example:**
```json
{
  "success": true,
  "timestamp": 1715001000
}
```

### 6.14 `settle` - Settle Liquids
* **Desc**: Force liquid settlement. Requires Admin.
* **Args**: None

**Response Data Example:**
```json
{
  "success": true
}
```

### 6.15 `help` - Get Command Help
* **Desc**: Get command list or specific usage.
* **Args**: None or `["<CommandName>"]`

**Response Data Example (List):**
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

### 6.16 `exportassets` - Export Assets
* **Desc**: Export game texture assets (Item/NPC/Buff etc.) to local. This is a **long-running** operation.
* **Args**: `["all"]` (Optional, exports all assets, otherwise only Core category)
* **Special Behavior**: Unlike other commands, this command sends **multiple** `command_response` packets with the same Request ID to update progress.

**Response Data Stream:**

**Packet 1 (Start):**
```json
{
  "type": "command_response",
  "message": "Start exporting 5000 assets to ...",
  "data": null,
  "id": "req-id-1"
}
```

**Packet 2...N (Progress):**
```json
{
  "type": "command_response",
  "message": "Exporting... 25% (1250/5000)",
  "data": null,
  "id": "req-id-1"
}
```

**Packet Final (Complete):**
```json
{
  "type": "command_response",
  "message": "Export complete! Processed 5000 assets.",
  "data": null,
  "id": "req-id-1"
}
```