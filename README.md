[中文 README](README_CN.md) | [English README](README.md) | [中文通信文档](TerraNoneBridge通信文档.md) | [English Protocol](TerraNoneBridge_Protocol.md)

<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-terralink

_✨ A NoneBot2 plugin for two-way communication between Terraria TModLoader servers and QQ Groups ✨_

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/newcovid/nonebot-plugin-terralink.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-terralink">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-terralink.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">

</div>

## 📖 Introduction

**TerraLink** is a NoneBot2 plugin designed to bridge Terraria TModLoader servers with QQ groups. Using the WebSocket protocol, it connects to the TML mod client to synchronize in-game chat and events to QQ groups in real-time. It also supports sending management commands from QQ to the game server, querying item recipes, viewing player inventories, and more.

### Core Features

- 🔗 **Two-way Communication**: Real-time sync of game chat ↔ QQ group messages.
- 🎨 **Rich Text Rendering**: Beautiful image responses based on HTML/CSS (Item details, Inventory, Recipe trees, etc.).
- 🎮 **Complete Command System**: Supports 16+ server management and query commands.
- 🔐 **Secure Authentication**: Token-based authentication system.
- 📱 **Multi-Server Support**: One Bot can manage multiple TML servers simultaneously.
- 🚀 **High Performance**: Built on asyncio and websockets.

## 💿 Installation

<details open>
<summary>Install using nb-cli</summary>

Open the command line in your nonebot2 project root and run:

```bash
nb plugin install nonebot-plugin-terralink
```

</details>

<details>
<summary>Install using package manager</summary>

In your nonebot2 plugin directory, run the appropriate command:

<details>
<summary>pip</summary>

```bash
pip install nonebot-plugin-terralink
```

</details>

</details>

## ⚙️ Configuration

Configure the following options in your NoneBot `.env` or `.env.prod` file:

```env
# Plugin Master Switch
terralink_enabled=true

# WebSocket Listening Port (TModLoader connects to this port)
terralink_port=7778

# Command Prefix (Used to identify commands in QQ groups)
terralink_cmd_prefix=/

# Resource path (Required, used to load local textures)
# How to obtain resources: Can only be obtained by installing the TerraNoneBridge mod in the game client. First, configure the mod configuration item "Custom export path".
# An example of "Custom export path" is: "D:\desktop\temp\tmodass". You need to create an empty folder for resource export, such as tmodass, so that resources will not be scattered into the upper directory.
# Use the "/tnb exportassets" command in single-player or local host mode to export resources, and manually place the resources in a location accessible to the server.
# Example: "/www/program/nonebot2/lolbot/data/terralink/tmodass" or "data/terralink/tmodass"
terralink_resource_path=""

# Group management settings file path. Leave empty to use data/terralink/group_settings.json
terralink_state_path=""

# Multi-Server Mapping List (JSON Format)
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
Export in-game resources (textures, etc.). This is a time-consuming operation. The Bot intercepts this command to prevent accidental triggers.
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
Force save the world.
- **Command**: `/save`

![save preview](/imgs/save.png)

#### 💧 `settle`
Force settle all liquids in the world.
- **Command**: `/settle`

![settle preview](/imgs/settle.png)

#### ⏰ `time`
Query or set the world time.
- **Command**: `/time [dawn/noon/dusk/midnight]`
- **Note**: Query time if no argument is provided; set time otherwise.

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
Query item details (stats, drops, NPC sales, simple recipes).
- **Command**: `/query <ItemName/ID>`
- **Aliases**: `查询`, `属性`

![query preview](/imgs/query.png)

#### 🔨 `recipe`
Generate a complete crafting tree image for an item, including all raw materials.
- **Command**: `/recipe <ItemName/ID>`
- **Aliases**: `合成`, `配方`

![recipe preview](/imgs/recipe.png)

#### 🔎 `search`
Fuzzy search for item names.
- **Command**: `/search <keyword>`
- **Aliases**: `搜索`, `查找`

![search preview](/imgs/search.png)

#### 📊 `tps`
View server performance status (TPS, memory, entity count, etc.).
- **Command**: `/tps`
- **Aliases**: `status`, `性能`

![tps preview](/imgs/tps.png)

---

## 💰 Sponsor

If you find this plugin helpful, consider buying the author a coffee ☕

<div align="center">
  <img src="/imgs/wechat.png" width="200" alt="WeChat Pay">
  <img src="/imgs/alipay.png" width="200" alt="Alipay">
</div>

## 📄 License

This project is licensed under the [MIT License](LICENSE).
