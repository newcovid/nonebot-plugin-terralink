[简体中文](README_CN.md) | [Protocol specification](TerraNoneBridge_Protocol.md)

<div align="center">

# nonebot-plugin-terralink

**A NoneBot2 integration layer for Terraria tModLoader servers**

[![License](https://img.shields.io/github/license/newcovid/nonebot-plugin-terralink.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/nonebot-plugin-terralink.svg)](https://pypi.org/project/nonebot-plugin-terralink/)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)

</div>

## Overview

**TerraLink** connects Terraria tModLoader servers to applications built with [NoneBot2](https://nonebot.dev/) through a documented WebSocket protocol. It exposes game-server events, operational controls, performance data, and game-content queries as bot-side capabilities that can be integrated into existing automation workflows.

The project consists of this NoneBot2 plugin and the companion [`TerraNoneBridge`](https://steamcommunity.com/sharedfiles/filedetails/?id=3617766364) tModLoader mod. The two components communicate through an authenticated protocol and can be deployed independently.

### Key capabilities

- **Bidirectional event bridge** — forward chat and server events between tModLoader and a configured bot conversation.
- **Server operations** — execute administrative actions such as saving the world, managing players, changing time, and cleaning hostile entities.
- **Game-data queries** — inspect items, recipes, inventories, progression, online players, and server status.
- **Structured rendering** — render inventories, item details, recipe trees, and operational data as HTML/CSS-based images.
- **Multi-server routing** — manage multiple tModLoader servers from a single NoneBot2 deployment.
- **Authenticated transport** — isolate server connections with per-link tokens.
- **Asynchronous architecture** — use `asyncio` and `websockets` for concurrent connections and event delivery.

## Architecture and adapter support

TerraLink separates the tModLoader protocol, connection management, rendering, and command services from the bot-platform-facing message handlers. This makes the core integration reusable when adding support for other NoneBot2 adapters.

The current release includes an **OneBot V11 group transport**. Its message events, group identifiers, and permission checks are adapter-specific. Supporting another NoneBot2 adapter requires a corresponding transport layer that maps that adapter's conversation and permission model onto TerraLink's existing core services; the tModLoader protocol and server-side integration do not need to be redesigned.

## Ecosystem and use cases

TerraLink extends a general-purpose bot framework into a game-server operations interface. Server operators can incorporate live tModLoader events, remote administration, monitoring, and game-data lookup into the same bot workflows they already use for moderation, notifications, scheduled tasks, and community operations.

By keeping the game-server protocol independent from the bot-facing transport, the project provides a practical foundation for additional adapters, management interfaces, and automation scenarios. The Python plugin is distributed through [PyPI](https://pypi.org/project/nonebot-plugin-terralink/), and the companion mod is available through the [Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3617766364).

## Installation

Using `nb-cli`:

```bash
nb plugin install nonebot-plugin-terralink
```

Using `pip`:

```bash
pip install nonebot-plugin-terralink
```

Install and configure the companion `TerraNoneBridge` mod on each tModLoader server that should connect to the bot.

## Configuration

Add the following options to the NoneBot `.env` or `.env.prod` file:

```env
# Plugin master switch
terralink_enabled=true

# WebSocket listening port used by TerraNoneBridge
terralink_port=7778

# Prefix for TerraLink commands in the bot conversation
terralink_cmd_prefix=/

# Local path containing textures exported by TerraNoneBridge
# Configure a custom export path in the mod, then run "/tnb exportassets"
# in single-player or local-host mode. Copy the exported files to a location
# accessible to the NoneBot2 process.
terralink_resource_path="data/terralink/tmodass"

# Persistent state file for per-conversation bridge controls
# Leave empty to use data/terralink/group_settings.json
terralink_state_path=""

# Server-to-conversation mappings
# In the current OneBot V11 transport, group_id is the destination group ID.
terralink_links=[
    {"token": "your_secret_token_1", "group_id": 123456789, "name": "Survival Server"},
    {"token": "your_secret_token_2", "group_id": 987654321, "name": "Calamity Server"}
]
```

Each `token` must match the token configured in the corresponding `TerraNoneBridge` instance.

## Commands

### Bridge controls

In the bundled OneBot V11 transport, these commands are available to the SuperUser, group owner, and group administrators. Settings are persisted per bound group.

- **Show status**: `/terralink status`
- **Toggle event forwarding**: `/terralink event <on/off>`
- **Toggle the complete bridge**: `/terralink bridge <on/off>`
- **Toggle bot-to-server chat**: `/terralink group <on/off>`
- **Toggle server-to-bot chat**: `/terralink server <on/off>`
- **Reset bridge settings**: `/terralink reset`
- **Aliases**: `tl`, `群服管理`

### Administrative commands

Administrative commands require NoneBot SuperUser permission.

#### `boss`

Show world progression and defeated bosses.

```text
/boss
```

![boss preview](/imgs/boss.png)

#### `buff`

Apply a buff to one player or all players.

```text
/buff <player/all> <BuffName> [seconds]
```

![buff preview](/imgs/buff.png)

#### `butcher`

Remove hostile entities from the server.

```text
/butcher
```

![butcher preview](/imgs/butcher.png)

#### `exportassets`

Request export of game assets. Because this operation can be expensive, the bot intercepts accidental remote execution.

```text
/export
/exportassets
```

#### `give`

Give an item to a player.

```text
/give <player> <ItemName> [amount]
```

![give preview](/imgs/give.png)

#### `kick`

Remove a player from the server.

```text
/kick <player> [reason]
```

![kick preview](/imgs/kick.png)

#### `save`

Force-save the current world.

```text
/save
```

![save preview](/imgs/save.png)

#### `settle`

Force world liquids to settle.

```text
/settle
```

![settle preview](/imgs/settle.png)

#### `time`

Query or change the world time.

```text
/time [dawn/noon/dusk/midnight]
```

![time preview](/imgs/time.png)

### Query commands

#### `help`

Display the command menu.

```text
/help
```

Aliases: `帮助`, `菜单`

![help preview](/imgs/help.png)

#### `inv`

Render a player's inventory, armor, and accessories.

```text
/inv <player>
```

Aliases: `inventory`, `查背包`

![inv preview](/imgs/inv.png)

#### `list`

List online players.

```text
/list
```

Aliases: `在线`, `who`, `ls`

![list preview](/imgs/list.png)

#### `query`

Show item statistics, drops, NPC sales, and direct recipes.

```text
/query <ItemName/ID>
```

Aliases: `查询`, `属性`

![query preview](/imgs/query.png)

#### `recipe`

Generate a complete crafting tree for an item.

```text
/recipe <ItemName/ID>
```

Aliases: `合成`, `配方`

![recipe preview](/imgs/recipe.png)

#### `search`

Search for item names.

```text
/search <keyword>
```

Aliases: `搜索`, `查找`

![search preview](/imgs/search.png)

#### `tps`

Show server performance, memory usage, and entity counts.

```text
/tps
```

Aliases: `status`, `性能`

![tps preview](/imgs/tps.png)

## Protocol

The communication contract between the plugin and `TerraNoneBridge` is documented in the [protocol specification](TerraNoneBridge_Protocol.md).

## License

Copyright © 2026 newcovid.

This project is licensed under the [GNU General Public License v3.0 only](LICENSE) (`GPL-3.0-only`).
