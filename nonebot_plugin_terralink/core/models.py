from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any, Union
import time

# =============================================================================
# 基础协议包 (WebSocket Packet Wrappers)
# 保持蛇形命名以匹配文档第 2-5 节的 Packet Header 定义
# =============================================================================


class BasePacket(BaseModel):
    """所有数据包的基类"""

    type: str
    timestamp: int = Field(default_factory=lambda: int(time.time()))


# --- 接收 (TML -> Nonebot) ---


class AuthPacket(BasePacket):
    type: Literal["auth"]
    token: str


class ChatPacket(BasePacket):
    type: Literal["chat"]
    user_name: str
    message: str
    color: Optional[str] = None


class EventPacket(BasePacket):
    type: Literal["event"]
    event_type: str
    world_name: str
    motd: Optional[str] = None


class CommandResponsePacket(BasePacket):
    type: Literal["command_response"]
    status: Literal["success", "error"]
    message: Optional[str] = None
    data: Optional[Any] = None
    id: Optional[str] = None


# --- 发送 (Nonebot -> TML) ---


class AuthResponsePacket(BasePacket):
    type: Literal["auth_response"] = "auth_response"
    success: bool
    message: str


class CommandPacket(BasePacket):
    type: Literal["command"] = "command"
    command: str
    args: List[str] = []
    id: Optional[str] = None


class ServerChatPacket(BasePacket):
    type: Literal["chat"] = "chat"
    user_name: str
    message: str
    color: Optional[str] = None


# =============================================================================
# 业务数据模型 (DTOs)
# 统一更新为小驼峰 (camelCase) 以匹配文档第 6 节
# =============================================================================


class CommandHelpDto(BaseModel):
    name: str
    description: str
    usage: Optional[str] = None
    permission: Optional[str] = None
    aliases: Optional[List[str]] = []


class TpsDto(BaseModel):
    version: str
    world: str
    tps: float
    onlineCount: int  # Updated
    npcCount: int  # Updated
    itemCount: int  # Updated
    memoryMb: float  # Updated
    gcMb: float  # Updated


class PlayerListDto(BaseModel):
    count: int
    max: int
    players: List[str]


class ItemDto(BaseModel):
    id: int
    name: str
    stack: int = 1
    prefix: Optional[str] = None
    imagePath: Optional[str] = None
    slot: Optional[int] = None
    # [Fix] 关键修复：添加 frameCount 字段，默认值为 1
    # 这样 Pydantic 就能正确解析 TML 发来的帧数数据，防止显示整张精灵图
    frameCount: int = 1


class PlayerInventoryDto(BaseModel):
    playerName: str
    inventory: List[ItemDto] = []
    armor: List[ItemDto] = []
    misc: List[ItemDto] = []
    piggy: Optional[List[ItemDto]] = []
    vault: Optional[List[ItemDto]] = []


# --- Search ---
class SearchResultItemDto(BaseModel):
    id: int  # Updated: ID -> id
    name: str  # Updated: Name -> name
    modName: str  # Updated: ModName -> modName
    matchQuality: int  # Updated: MatchQuality -> matchQuality
    imagePath: Optional[str] = None  # Updated: ImagePath -> imagePath
    frameCount: int = 1  # Updated: FrameCount -> frameCount


class SearchResultDto(BaseModel):
    query: str
    count: int
    results: List[SearchResultItemDto] = []


# --- Query (Item Details) ---
class RecipeIngredientDto(BaseModel):
    id: int
    name: str
    stack: int
    imagePath: Optional[str] = None
    frameCount: int = 1


class RecipeStationDto(BaseModel):
    id: int
    name: str
    stack: int = 1
    imagePath: Optional[str] = None
    frameCount: int = 1


class QueryRecipeDto(BaseModel):
    resultName: str
    resultCount: int
    stations: List[RecipeStationDto] = []
    ingredients: List[RecipeIngredientDto] = []


class ItemStatsDto(BaseModel):
    damage: int = 0
    defense: int = 0
    crit: int = 0
    useTime: int = 0
    knockBack: float = 0.0
    value: int = 0
    autoReuse: bool = False
    consumable: bool = False
    maxStack: int = 1


class ItemDetailDto(BaseModel):
    id: int
    name: str
    mod: str
    type: str
    imagePath: Optional[str] = None
    frameCount: int = 1
    stats: Optional[ItemStatsDto] = None
    description: Optional[str] = None
    droppedBy: List[Dict[str, Any]] = []
    soldBy: List[Dict[str, Any]] = []
    recipes: List[QueryRecipeDto] = []


# --- Recipe (Tree) - 全部更新为小驼峰 ---
class ItemNodeDto(BaseModel):
    id: int  # Updated
    name: str  # Updated
    imagePath: Optional[str] = None  # Updated
    mod: str  # Updated
    frameCount: int = 1  # Updated


class RecipeStationTileDto(BaseModel):
    tileId: int  # Updated: TileId -> tileId
    name: str  # Updated
    imagePath: Optional[str] = None  # Updated


class RecipeIngredientSimpleDto(BaseModel):
    itemId: int  # Updated: ItemId -> itemId
    count: int  # Updated: Count -> count
    groupName: Optional[str] = None
    groupIds: Optional[List[int]] = None  # Updated: Added per doc


class RecipeDto(BaseModel):
    recipeId: int  # Updated
    resultId: int  # Updated
    resultCount: int  # Updated
    stations: List[RecipeStationTileDto] = []  # Updated: Stations -> stations
    conditions: List[str] = []  # Updated: Conditions -> conditions
    ingredients: List[RecipeIngredientSimpleDto] = (
        []
    )  # Updated: Ingredients -> ingredients


class RecipeDataDto(BaseModel):
    targetId: int  # Updated
    nodes: Dict[str, ItemNodeDto] = {}  # Updated
    craftRecipes: List[RecipeDto] = []  # Updated
    usageRecipes: List[RecipeDto] = []  # Updated


class BossStatusDto(BaseModel):
    name: str
    isDowned: bool
    type: str


class BossProgressDto(BaseModel):
    worldName: str
    difficulty: str
    defeated: List[BossStatusDto] = []
    undefeated: List[BossStatusDto] = []


class TimeDto(BaseModel):
    timeString: str  # Updated: time_string -> timeString
    isDay: bool  # Updated: is_day -> isDay
    moonPhase: str  # Updated: moon_phase -> moonPhase
    moonPhaseId: int = 0  # Added
    rawTime: float = 0.0  # Added
    action: str


class ActionResponseDto(BaseModel):
    target: Optional[str] = None
    success: Optional[bool] = None
    reason: Optional[str] = None
    item: Optional[str] = None
    amount: Optional[int] = None
    buff: Optional[str] = None
    duration: Optional[int] = None
    killedCount: Optional[int] = None  # Updated: Added for butcher command
