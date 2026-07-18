[中文 README](README_CN.md) | [English README](README.md) | [中文通信文档](TerraNoneBridge通信文档.md) | [English Protocol](TerraNoneBridge_Protocol.md)

<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-terralink

_✨ A NoneBot2 plugin for two-way communication between Terraria tModLoader servers and QQ groups ✨_

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/newcovid/nonebot-plugin-terralink.svg" alt="license">
</a>
<a href="https://pypi.org/project/nonebot-plugin-terralink/">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-terralink.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">

</div>

## 📖 Introduction

**TerraLink** is a NoneBot2 plugin designed to bridge Terraria tModLoader servers with QQ groups. Using the WebSocket protocol, it connects to the companion TML mod to synchronize in-game chat and events to QQ groups in real time. It also supports sending management commands from QQ to the game server, querying item recipes, viewing player inventories, and more.

### Core Features

- 🔗 **Two-way Communication**: Real-time sync of game chat ↔ QQ group messages.
- 🎨 **Rich Text Rendering**: Image responses based on HTML/CSS for item details, inventories, recipe trees, and other structured data.
- 🎮 **Complete Command System**: Supports 16+ server-management and query commands.
- 🔐 **Secure Authentication**: Token-based authentication between the bot and game server.
- 📱 **Multi-Server Support**: One bot can manage multiple tModLoader servers simultaneously.
- 🚀 **Asynchronous Architecture**: Built on `asyncio` and `websockets`.

## 🌍 Reach and Impact

TerraLink maintains an open-source interoperability layer between three distinct ecosystems: **NoneBot2/OneBot bots, QQ group communities, and Terraria tModLoader servers**. It addresses a specialized integration gap that is not covered by either ecosystem on its own.

- **Public distribution**: The Python plugin is released on [PyPI](https://pypi.org/project/nonebot-plugin-terralink/), while the companion `TerraNoneBridge` mod is distributed through the [Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3617766364).
- **Operational scope**: The project combines bidirectional chat, event forwarding, remote administration, server monitoring, item and recipe queries, inventory rendering, authentication, and multi-server routing.
- **Reusable protocol boundary**: The communication contract is documented in both [Chinese](TerraNoneBridge通信文档.md) and [English](TerraNoneBridge_Protocol.md), making the integration auditable and easier to extend.
- **Bilingual maintenance**: User-facing setup, configuration, command references, and protocol documentation are maintained in both Chinese and English.
- **Community infrastructure**: The project is intended for self-hosted game-server operators and community maintainers who need reliable communication between in-game services and external group-management workflows.

Adoption and release evidence is kept on the linked public distribution pages rather than hard-coded here, so the figures remain current and independently verifiable.

## 💿 Installation

<details open>
<summary>Install using nb-cli</summary>

Open the command line in your NoneBot2 project root and run:

```bash
nb plugin install nonebot-plugin-terralink
```

</details>

<details>
<summary>Install using a package manager</summary>

In your NoneBot2 project, run:

```bash
pip install nonebot-plugin-terralink
```

</details>

## ⚙️ Configuration

Configure the following options in your NoneBot `.env` or `.env.prod` file:

```env
# Plugin master switch
terralink_enabled=true

# WebSocket listening port (the tModLoader side connects to this port)
terralink_port=7778

# Command prefix used in QQ groups
terralink_cmd_prefix=/

# Resource path (required for loading local textures)
# Resources can only be exported by installing the TerraNoneBridge mod in a game client.
# Configure the mod's custom export path first, create an empty export directory,
# and run "/tnb exportassets" in single-player or local-host mode.
# Then place the exported resources somewhere accessible to the bot server.
# Examples: "/www/program/nonebot2/lolbot/data/terralink/tmodass"
#           "data/terralink/tmodass"
terralink_resource_path=""

# Persistent group-management state file. Leave empty to use
# data/terralink/group_settings.json
terralink_state_path=""

# Multi-server mapping list (JSON format)
terralink_links=[
    {"token": "your_secret_token_1", "group_id": 123456789, "name": "Survival Server"},
    {"token": "your_secret_token_2", "group_id": 987654321, "name": "Calamity Server"}
]
```

---

## 💻 Commands

### 0. Group Management Commands (SuperUser / Group Owner / Group Admin)

Control TerraLink forwarding behavior per QQ group. Settings are persisted. All switches are enabled by default to preserve existing behavior.

- **Show status**: `/terralink status`
- **Toggle event broadcasts**: `/terralink event <on/off>`
- **Toggle two-way chat bridge**: `/terralink bridge <on/off>`
- **Toggle QQ group to server chat only**: `/terralink group <on/off>`
- **Toggle server to QQ group chat only**: `/terralink server <on/off>`
- **Reset group settings**: `/terralink reset`
- **Aliases**: `tl`, `群服管理`

### 1. Admin Commands (SuperUser Only)

#### 💀 `boss`
Check the boss defeat progress of the current world.
- **Command**: `/boss`
- **Aliases**: `bosses`, `进度`

![boss preview](/imgs/boss.png)

#### 💊 `buff`
Give a buff to a specific player or all players.
- **Command**: `/buff <player/all> <BuffName> [seconds]`

![buff preview](/imgs/buff.png)

#### 🗡️ `butcher`
Kill all hostile mobs in the server.
- **Command**: `/butcher`

![butcher preview](/imgs/butcher.png)

#### 📤 `exportassets`
Export in-game resources such as textures. This is a time-consuming operation, and the bot intercepts the command to prevent accidental triggers.
- **Command**: `/export` or `/exportassets`

#### 🎁 `give`
Give items to a specific player.
- **Command**: `/give <player> <ItemName> [amount]`

![give preview](/imgs/give.png)

#### 🦵 `kick`
Kick a player from the server.
- **Command**: `/kick <player> [reason]`

![kick preview](/imgs/kick.png)

#### 💾 `save`
Force-save the world.
- **Command**: `/save`

![save preview](/imgs/save.png)

#### 💧 `settle`
Force all liquids in the world to settle.
- **Command**: `/settle`

![settle preview](/imgs/settle.png)

#### ⏰ `time`
Query or set the world time.
- **Command**: `/time [dawn/noon/dusk/midnight]`
- **Note**: Query the time when no argument is provided; set it otherwise.

![time preview](/imgs/time.png)

---

### 2. Query Commands (Available to All Users)

#### 📖 `help`
Show the command help menu.
- **Command**: `/help`
- **Aliases**: `帮助`, `菜单`

![help preview](/imgs/help.png)

#### 🎒 `inv`
View a player's inventory, armor, and accessories.
- **Command**: `/inv <player>`
- **Aliases**: `inventory`, `查背包`

![inv preview](/imgs/inv.png)

#### 👥 `list`
Show the list of currently online players.
- **Command**: `/list`
- **Aliases**: `在线`, `who`, `ls`

![list preview](/imgs/list.png)

#### 🔍 `query`
Query item details, including stats, drops, NPC sales, and simple recipes.
- **Command**: `/query <ItemName/ID>`
- **Aliases**: `查询`, `属性`

![query preview](/imgs/query.png)

#### 🔨 `recipe`
Generate a complete crafting-tree image for an item, including all raw materials.
- **Command**: `/recipe <ItemName/ID>`
- **Aliases**: `合成`, `配方`

![recipe preview](/imgs/recipe.png)

#### 🔎 `search`
Fuzzy-search item names.
- **Command**: `/search <keyword>`
- **Aliases**: `搜索`, `查找`

![search preview](/imgs/search.png)

#### 📊 `tps`
View server-performance status, including TPS, memory, and entity counts.
- **Command**: `/tps`
- **Aliases**: `status`, `性能`

![tps preview](/imgs/tps.png)

---

## 📄 License

Copyright © 2026 newcovid.

This project is licensed under the [GNU General Public License v3.0 only](LICENSE) (`GPL-3.0-only`).
