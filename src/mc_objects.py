from itertools import chain

from respackopts import escape_quotes
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Literal, Self, overload
import re
from logging import getLogger

# Executing this will cause cicular dependency
# Or as I would like to call it, Ouroborous dependency
if TYPE_CHECKING:
    from commands import Command

_MISSING = object()

type ColorName = Literal["black", "dark_blue", "dark_green", "dark_aqua", "dark_red", 
                         "dark_purple", "gold", "gray", "dark_gray", "blue", "green", 
                         "aqua", "red", "light_purple", "yellow", "white"]

logger = getLogger("disc_gen/mc_object")

class Relative[N: int | float]:
    """Represents a relative world coordinate component.
    
    Describes an offset from execution position along one of the world 
    axes, and a lone tilde assumes an offset of `0`.
    
    Evalutes to ~n.
    
    Note: Local coordinates cannot be mixed with world coordinates. You can try modify the rotation
    of the executor using `/execute rotated` to 'globalize' the Y coordinate.
    """
    def __init__(self, n: N = 0):
        self.n = n
    def __str__(self): return f"~{self.n if self.n else ""}"
class Local[N: int | float]:
    """Represents a local coordinate component.
    
    Describes an offset within a moving, entity-centric frame, relative to your rotation.
    
    +Z directs forward in the direction the executor faces, +X directs to its left, 
    +Y directs upward.
    
    Described in other terms, these coordinates express '^ΔSway ^ΔHeave ^ΔSurge'.
    
    For example, `/tp ^ ^ ^5` teleports you 5 blocks forward.
    
    Evaluates to `^n`.
    
    Note:
    1. Local coordinates cannot be mixed with world coordinates. You can try modify the rotation
    of the executor using `/execute rotated` to 'globalize' the Y axis, or the X/Z axis.
    2. When rotation is `0 0`, `^` acts the same as `~`.
    """
    def __init__(self, n: N = 0):
        self.n = n
    def __str__(self): return f"^{self.n if self.n else ""}"

type RelatableCoordComponent[T: int | float] = T | Relative[T] | Local[T]
type BlockPos = Vec3[RelatableCoordComponent[int]]
type Position = Vec3[RelatableCoordComponent[float]]
type NonDependentPosition = Vec3[float]
class Vec3[T]:
    def __init__(self, x: T, y: T, z: T):
        self.x = x
        self.y = y
        self.z = z
    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z
    def __str__(self):
        return f"{self.x} {self.y} {self.z}"

class Rotation:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

class Color:
    BLACK: Color
    DARK_BLUE: Color
    DARK_GREEN: Color
    DARK_AQUA: Color
    DARK_RED: Color
    DARK_PURPLE: Color
    GOLD: Color
    GRAY: Color
    DARK_GRAY: Color
    BLUE: Color
    GREEN: Color
    AQUA: Color
    RED: Color
    LIGHT_PURPLE: Color
    YELLOW: Color
    WHITE: Color
    
    intended_representation: Literal["hex_rgb"] = "hex_rgb"
    def __init__(self, r: int, g: int, b: int, a: int):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def to_hex_rgb(self):
        return f"#{self.r:X}{self.g:X}{self.b:X}"
    
    def to_hex_rgba(self):
        return f"#{self.r:X}{self.g:X}{self.b:X}{self.a:X}"
    
    def to_hex_rgba(self):
        return f"#{self.a:X}{self.r:X}{self.g:X}{self.b:X}"

    def __str__(self):
        return {
            "hex_rgb": self.to_hex_rgb()
        }

    @staticmethod
    def from_name(name: ColorName):
        return {
            "black": Color.BLACK,
            "dark_blue": Color.DARK_BLUE,
            "dark_green": Color.DARK_GREEN,
            "dark_aqua": Color.DARK_BLUE,
            "dark_red": Color.DARK_RED,
            "dark_purple": Color.DARK_PURPLE,
            "gold": Color.GOLD,
            "gray": Color.GRAY,
            "dark_gray": Color.DARK_GRAY,
            "blue": Color.BLUE,
            "green": Color.GREEN,
            "aqua": Color.AQUA,
            "red": Color.RED,
            "light_purple": Color.LIGHT_PURPLE,
            "yellow": Color.YELLOW,
            "white": Color.WHITE
        }[name]
    @staticmethod
    def from_rgba_component(r: int, g: int, b: int, a: int = 255):
        return Color(r, g, b, a)
    
    @staticmethod
    def from_rgb_component(r: int, g: int, b: int):
        return Color(r, g, b, 255)

    @staticmethod
    def from_rgba(h: int | str) -> Color:
        """Evaluates a RGBA/HEX code.
        
        Accepts a hex string (`#RRGGBBAA`) or a number (`0xRRGGBBAA`).
        """
        if isinstance(h, str):
            h = int(h.removeprefix("#"), 16)
        
        return Color(
            (h >> 24) & 0xFF,
            (h >> 16) & 0xFF,
            (h >> 8) & 0xFF,
            h & 0xFF,
        )
    
    @staticmethod
    def from_argb(h: int | str) -> Color:
        """Evaluates a ARGB/HEX code.
        
        Accepts a hex string (`#AARRGGBB`) or a number (`0xAARRGGBB`).
        """
        if isinstance(h, str):
            h = int(h.removeprefix("#"), 16)
        
        return Color(
            a = (h >> 24) & 0xFF,
            r = (h >> 16) & 0xFF,
            g =(h >> 8) & 0xFF,
            b = h & 0xFF,
        )
    
    @staticmethod
    def from_rgb(h: int | str) -> Color:
        """Evaluates a RGB/HEX code.
                
        Accepts a hex string (`#RRGGBB`) or a number (`0xRRGGBB`).
        """
        if isinstance(h, str):
            h = int(h.removeprefix("#"), 16)
        
        return Color.from_rgb_component(
            (h >> 16) & 0xFF,
            (h >> 8) & 0xFF,
            h & 0xFF
        )

Color.BLACK = Color.from_rgb(0x000000)
Color.DARK_BLUE = Color.from_rgb(0x0000AA)
Color.DARK_GREEN = Color.from_rgb(0x00AA00)
Color.DARK_AQUA = Color.from_rgb(0x00AAAA)
Color.DARK_RED = Color.from_rgb(0xAA0000)
Color.DARK_PURPLE = Color.from_rgb(0xAA00AA)
Color.GOLD = Color.from_rgb(0xFFAA00)
Color.GRAY = Color.from_rgb(0xAAAAAA)
Color.DARK_GRAY = Color.from_rgb(0xC6C6C6)
Color.BLUE = Color.from_rgb(0x5555FF)
Color.GREEN = Color.from_rgb(0x55FF55)
Color.AQUA = Color.from_rgb(0x55FFFF)
Color.RED = Color.from_rgb(0xFF5555)
Color.LIGHT_PURPLE = Color.from_rgb(0xFF55FF)
Color.YELLOW = Color.from_rgb(0xFFFF55)
Color.WHITE = Color.from_rgb(0xFFFFFF)


class NBT:
    """Base class of all NBT data types."""
    @staticmethod
    def to_nbt(o: object):
        if isinstance(o, dict):
            return NBTCompound({k: NBT.to_nbt(v) for k, v in o.items()})
        if isinstance(o, list):
            return NBTList([NBT.to_nbt(i) for i in o])
        if isinstance(o, bool):
            return NBTBoolean(o)
        if isinstance(o, int):
            return NBTInt(o)
        if isinstance(o, float):
            return NBTDouble(o)

class NBTByte(NBT):
    def __init__(self, v: int):
        assert -128 <= v <= 127
        self._v = v
    def __str__(self): return f"{self._v}b"
class NBTBoolean(NBT):
    """Represent the boolean type ('true' and 'false')"""
    def __init__(self, v: bool):
        self._v = v
    def __str__(self): return str(self._v).lower()
class NBTShort(NBT):
    def __init__(self, v: int) -> None:
        assert -32768 <= v <= 32767
        self._v = v
    def __str__(self) -> str: return f"{self._v}s"
class NBTInt(NBT):
    def __init__(self, v: int) -> None:
        self._v = v
    def __str__(self) -> str: return f"{self._v}"
class NBTLong(NBT):
    def __init__(self, v: int) -> None:
        self._v = v
    def __str__(self) -> str: return f"{self._v}L"
class NBTFloat(NBT):
    def __init__(self, v: float) -> None:
        self._v = v
    def __str__(self) -> str: return f"{self._v}f"
class NBTDouble(NBT):
    def __init__(self, v: float) -> None:
        self._v = v
    def __str__(self) -> str: return f"{self._v}D"
class NBTString(NBT):
    def __init__(self, v: str) -> None:
        self._v = v
    def __str__(self) -> str: return f'"{escape_quotes(self._v)}"'
class NBTList(NBT):
    """Represent a general NBT list."""
    def __init__(self, v: list[NBT]) -> None:
        self._v = v
    def __str__(self): return f"[{",".join(str(i) for i in self._v)}]"
class NBTCompound(NBT):
    """Represent a key-value map NBT."""
    def __init__(self, v: dict[str, NBT]) -> None:
        self._v = v
    def get(self, v: str, default: Any) -> Any:
        return self._v.get(v, default)
    def __getitem__(self, item) -> str:
        return self._v[item]
    def __setitem__(self, item, value):
        self._v[item] = value
    def __str__(self):
        return "{%s}" % ",".join(
            f"{k if re.match(r"[\w\d\_\-+\.]+", k) else escape_quotes(k)}:{v}" for k, v in self._v.items()
        )

type TextComponentObj = str | TextComponent | list[TextComponent]
class TextComponent:
    """Represent a NBT-compound-style text component.
    
    If you want to convert aliases, use the `.expand()` class method.
    """
    def __init__(self):
        self._internal_d = NBTCompound({})
    def to_nbt(self):
        return self._internal_d
    def __str__(self): return str(self.to_nbt())
    
    @classmethod
    def expand(cls, thing: TextComponentObj) -> TextComponent:
        """Transforms a text component object alias to a `TextComponent`."""
        if isinstance(thing, list):
            return cls.from_list(thing)
        if isinstance(thing, TextComponent):
            return thing
        if isinstance(thing, str):
            return cls().text(thing)
        raise ValueError(f"Can't parse the following value to a text component: '{thing}'")
    
    @classmethod
    def from_list(cls, l: list[TextComponentObj]) -> TextComponent:
        match len(l):
            case 0:
                return cls().text("")
            case 1:
                return cls.expand(l[0])
            case _:
                return cls.expand(l[0]).extra(*l[1:])
    
    def text(self, text: str):
        if self._internal_d.get("type", "text") != "text":
            logger.warning(
                "Conflicting types in text component ('%s' with 'text'). This may cause unintended consequences.",
                self._internal_d["type"]
            )
        self._internal_d["type"] = NBTString("text")
        self._internal_d["text"] = NBTString(text)
        return self
    
    def translatable(self, translate: str, fallback: str | None = None, with_: list[TextComponent] | None = None):
        if self._internal_d.get("type", "translatable") != "translatable":
            logger.warning(
                "Conflicting types in text component ('%s' with 'translatable'). This may cause unintended consequences.",
                self._internal_d["type"]
            )
        self._internal_d["type"] = NBTString("translatable")
        self._internal_d["translate"] = NBTString(translate)
        if fallback is not None:
            self._internal_d["fallback"] = NBTString(fallback)
        if with_ is not None:
            self._internal_d["with"] = NBTList(with_)
        return self
    
    def score(self, name: TargetSelector | str, objective: str):
        self._internal_d["score"] = NBTCompound({"name": str(name), "objective": objective})
        return self
    
    def color(self, color: str | int | Color, /):
        if isinstance(color, int):
            self._internal_d["color"] = NBTString(f"#{color:x}")
        elif isinstance(color, Color):
            self._internal_d["color"] = NBTString(color.to_hex_rgb())
        elif isinstance(color, str):
            self._internal_d["color"] = NBTString(color)
        else:
            assert False
        return self
    
    def italic(self, i: bool, /):
        self._internal_d["italic"] = NBTBoolean(i)
        return self
    
    def bold(self, b: bool, /):
        self._internal_d["bold"] = NBTBoolean(b)
        return self
    
    def underlined(self, u: bool, /):
        self._internal_d["underlined"] = NBTBoolean(u)
        return self
    
    def strikethrough(self, s: bool, /):
        self._internal_d["strikethrough"] = NBTBoolean(s)
        return self
    
    def obfuscated(self, o: bool, /):
        self._internal_d["obfuscated"] = NBTBoolean(o)
        return self
    
    def extra(self, *comps: TextComponent):
        self._internal_d["extra"] = NBTList(list(chain(self._internal_d._v.get("extra", []), (comps))))
        return self
    
    @overload
    def click_event(self, type: Literal[ClickEvent.OPEN_URL], url: str) -> Self: ...
    
    @overload
    def click_event(self, type: Literal[ClickEvent.RUN_COMMAND], command: str) -> Self: ...
    
    @overload
    def click_event(self, type: Literal[ClickEvent.SUGGEST_COMMAND], command: str) -> Self: ...
    
    @overload
    def click_event(self, type: Literal[ClickEvent.CHANGE_PAGE], page: int) -> Self: ...
    
    @overload
    def click_event(self, type: Literal[ClickEvent.COPY_TO_CLIPBOARD], value: str) -> Self: ...
    
    @overload
    def click_event(self, type: Literal[ClickEvent.SHOW_DIALOG], dialog: str) -> Self: ...
    
    @overload
    def click_event(self, type: Literal[ClickEvent.CUSTOM], id, payload) -> Self: ...
    
    def click_event(self, type: ClickEvent, _1: Any = _MISSING, _2: Any = _MISSING, /, *,
                    url: str = _MISSING, command: Command | str = _MISSING, page: int = _MISSING, value: str = _MISSING, 
                    dialog: str = _MISSING, id = _MISSING, payload = _MISSING):
        d = {"action": str(type)}
        def _choose(pos, keyword, name: str):
            if pos is _MISSING and keyword is _MISSING:
                raise ValueError(f"'{name}' must be provided")

            if pos is not _MISSING and keyword is not _MISSING:
                raise ValueError(
                    f"'{name}' was provided both positionally and by keyword "
                    f"(positional={pos!r}, keyword={keyword!r})"
                )

            return pos if pos is not _MISSING else keyword
        
        match type:
            case ClickEvent.OPEN_URL:
                d["url"] = NBTString(_choose(_1, url, "url"))

            case ClickEvent.RUN_COMMAND | ClickEvent.SUGGEST_COMMAND:
                d["command"] = NBTString(_choose(_1, command, "command"))

            case ClickEvent.CHANGE_PAGE:
                d["page"] = NBTString(_choose(_1, page, "page"))

            case ClickEvent.COPY_TO_CLIPBOARD:
                d["value"] = NBTString(_choose(_1, value, "value"))

            case ClickEvent.SHOW_DIALOG:
                d["dialog"] = NBTString(_choose(_1, dialog, "dialog"))

            case ClickEvent.CUSTOM:
                d["id"] = NBTString(_choose(_1, id, "id"))
                d["payload"] = NBTString(_choose(_2, payload, "payload"))

            case _:
                raise ValueError(f"Invalid click event type: {type!r}")

        self._internal_d["click_event"] = NBTCompound(d)
        return self

class ClickEvent(StrEnum):
    """An enum to represent different types of clicking actions.
    
    Used by `TextComponent`'s `click_event` action.
    
    **Note:** `open_file` is delibarately absent because you can't use it in a datapack.
    """
    OPEN_URL = "open_url"
    RUN_COMMAND = "run_command"
    SUGGEST_COMMAND = "suggest_command"
    CHANGE_PAGE = "change_page"
    COPY_TO_CLIPBOARD = "copy_to_clipboard"
    SHOW_DIALOG = "show_dialog"
    CUSTOM = "custom"

type IntOrIntRange = IntRange | int
class IntRange:
    def __init__(self, min: int | None = None, max: int | None = None):
        if min == None and max == None:
            raise ValueError("'min' and 'max' must not both be 'None'")
        self.min = min
        self.max = max
    
    def __str__(self):
        return f"{"" if self.min is None else self.min}..{"" if self.max is None else self.max}"
    
    def __contains__(self, item):
        return self.min <= item <= self.max
    
    @classmethod
    def max(cls, max): return cls(None, max)
    
    @classmethod
    def min(cls, min): return cls(min, None)

type FloatOrFloatRange = FloatRange | float
class FloatRange:
    
    def __init__(self, min: float | None, max: float | None):
        if self.min == None and self.max == None:
            raise ValueError("'min' and 'max' must not both be 'None'")
        self.min = min
        self.max = max
    
    def __str__(self):
        return f"{"" if self.min is None else self.min}..{"" if self.max is None else self.max}"
    
    def __contains__(self, item):
        return self.min <= item <= self.max

class TargetSelector:
    tag: str
    
    def __init__(self):
        self._arguments = {}
    
    def _add(self, arg: str, val):
        if arg in self._arguments:
            raise ValueError(...)
        self._arguments[arg] = val
        return self
    
    def _add_allow_dup(self, arg: str, val):
        self._arguments[arg] = val
        return self
    
    def x(self, v: float):
        return self._add("x", v)
    
    def y(self, v: float):
        return self._add("y", v)
    
    def z(self, v: float):
        return self._add("z", v)
    
    def distance(self, v: FloatOrFloatRange):
        return self._add("distance", v)
    
    def scores(self, scores: dict[str, IntOrIntRange]):
        return self._add("scores", "{%s}" % ",".join(f"{k}={v}" for k, v in scores.items()))
    
    def predicate(self, predicate: str) -> Self:
        return self._add_allow_dup("predicate", predicate)
    
    def predicate_not(self, predicate: str) -> Self:
        return self._add_allow_dup("predicate", f"!{predicate}")
    
    def __str__(self):
        return f"@{self.tag}" + ("" if not self._arguments else f"[{",".join(f"{k}={v}" for k, v in self._arguments.items())}]")

class NearestPlayer(TargetSelector):
    tag = "p"

class AllPlayers(TargetSelector):
    tag = "a"

class AllEntities(TargetSelector):
    tag = "e"

class RandomPlayer(TargetSelector):
    tag = "r"

class NearestEntity(TargetSelector):
    tag = "n"

class Executor(TargetSelector):
    tag = "s"

class Relation(StrEnum):
    """Entities related to another entity.
    Has the following:
    - `attacker`: the last entity that damaged the current executor entity 
    in the previous 5 seconds. Note that damage types in `minecraft:no_anger` 
    tag bypass the record of attacker. Interaction entities do not forget 
    attacker after 5 seconds. Some mobs forget the attacker when ceasing 
    their aggression.
    - `controller`: the entity that is riding and controlling the current executor entity.
    - `leasher`: the entity leading the current executor entity with a leash.
    - `origin`: the entity that causes the summon of the current executor entity.
    For example, the shooter of an arrow, the primer of a primed TNT entity.
    - `owner`: the owner of the current executor entity if it is a tameable animal.
    - `passengers`: all entities that are directly riding the current executor entity, 
    no sub-passengers.
    - `target`: the target that the current executor entity intends on attacking. 
    Interaction entities can select the last entity that interacted with them.
    - `vehicle`: the entity ridden by the current executor entity.
    """
    ATTACKER = "attacker"
    CONTROLLER = "controller"
    LEASHER = "leasher"
    ORIGIN = "origin"
    OWNER = "owner"
    PASSENGERS = "passengers"
    TARGET = "target"
    VEHICLE = "vehicle"

# How did I not know this syntax before wtf lmao
type Entity = TargetSelector | str
type ScoreHolder = Entity | Literal["*"]
type Compare = Literal["<", "<=", "=", ">=", ">"]

class Heightmap(StrEnum):
    """Heightmaps are maps to store the Y-level of the highest block at each horizontal coordinate.
    
    The following heightmaps are supported:
    - `WORLD_SURFACE`: Stores the Y-level of the highest non-air (all types of air) block.
    - `WORLD_SURFACE_WG`: Stores the Y-level of the highest non-air (all types of air) block. 
    Used only during world generation.
    - `OCEAN_FLOOR`: Stores the Y-level of the highest block whose material blocks motion. 
    Used only on the server side.
    - `OCEAN_FLOOR_WG`: Stores the Y-level of the highest block whose material blocks motion. 
    Used only during world generation.
    - `MOTION_BLOCKING`: Stores the Y-level of the highest block whose material blocks motion 
    or blocks that contains a fluid (water, lava, or waterlogged blocks).
    - `MOTION_BLOCKING_NO_LEAVES`: Stores the Y-level of the highest block whose material blocks 
    motion, or blocks that contains a fluid (water, lava, or waterlogged blocks), except various 
    leaves. Used only on the server side, e.g. for pillager patrol spawning.
    """
    WORLD_SURFACE = "WORLD_SURFACE"
    WORLD_SURFACE_WG = "WORLD_SURFACE_WG"
    OCEAN_FLOOR = "OCEAN_FLOOR"
    OCEAN_FLOOR_WG = "OCEAN_FLOOR_WG"
    MOTION_BLOCKING = "MOTION_BLOCKING"
    MOTION_BLOCKING_NO_LEAVES = "MOTION_BLOCKING_NO_LEAVES"

# Compound criteria exists, ok?
type ScoreboardCriteria = ScoreboardSingleCriteria | str
class ScoreboardSingleCriteria(StrEnum):
    DUMMY = "dummy"
    TRIGGER = "trigger"
    DEATH_COUNT = "deathCount"
    PLAYER_KILL_COUNT = "playerKillCount"
    TOTAL_KILL_COUNT = "totalKillCount"
    HEALTH = "health"
    XP = "xp"
    LEVEL = "level"
    FOOD = "food"
    AIR = "air"
    ARMOR = "armor"