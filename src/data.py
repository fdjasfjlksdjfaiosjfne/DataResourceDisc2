from dataclasses import FrozenInstanceError, dataclass, is_dataclass, field, InitVar, fields
import dataclasses
import functools
from typing import Any, Callable, Final, Literal, cast, ClassVar, NewType, TYPE_CHECKING
from functools import cache
from pathlib import Path
from logging import getLogger
from pydub import AudioSegment
from respackopts import FORMATTING_LIST
from json5 import load as json5_load, dump as json5_dump, dumps as json5_dumps, JSON5Encoder, QuoteStyle
from json import JSONDecodeError
from respackopts import mu_enum_equals, mu_enum_nequals, mu_ternary
import sys

# I could remove `functools.update.wrapper` but this is funnier
@lambda f: functools.update_wrapper(object.__setattr__, f) if TYPE_CHECKING else object.__setattr__
def forcesetattr(self: object, name: str, value: Any) -> None:
    "An alias to `object.__setattr__()`. Just don't look at its truely majestic declaration for too long."

class classproperty:
    def __init__(self, f: classmethod | Callable): 
        self.f = f if isinstance(f, classmethod) else classmethod(f)
    def __get__(self, obj, cls):
        return self.f.__wrapped__(cls)

class staticproperty:
    def __init__(self, f: staticmethod | Callable): 
            self.f = f if isinstance(f, staticmethod) else staticmethod(f)
    def __get__(self, obj, cls):
        return self.f.__wrapped__()

class DataJSONEncoder(JSON5Encoder):
    def default(self, o):
        from commands import Command
        if isinstance(o, Command):
            logger.debug(f"JSON encoder encoding command {o!s}")
            return str(o)
        if is_dataclass(o):
            return {field.name: getattr(o, field.name) for field in fields(o) if field.metadata.get("serialize", True)}
        if isinstance(o, Path):
            return str(o)
        return super().default(o)

ROOT = Path(__file__).parent.parent
logger = getLogger("disc_gen/data")

DiscID = NewType("DiscID", str)

@cache
def to_camel_case(s: str) -> str:
    parts = s.replace("-", "_").split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])

DATA: Data = None
OMNIDISC: Path = ROOT / "data/omnidisc.json"

def init(data_jsons: list[Path]):
    global DATA
    global MISSING_DISC
    # data.json
    for path in data_jsons:
        if not path.exists():
            logger.warning(
                "Data file '%s' not found, checking for alternatives...",
                path
            )
            continue
        with open(path, encoding = "utf-8") as f:
            try:
                d = json5_load(f)
            except JSONDecodeError:
                logger.critical("'%s' contains invalid JSON, error dump below", path)
                raise
            DATA = Data(**d)
            if DATA.critical_errors:
                raise ValueError("While parsing data, the following critical errors are found:\n" + "\n".join(DATA.critical_errors), DATA.critical_errors)
            logger.info("Retrieve data successfully.")
            break
    else:
        logger.critical("Required data file not found.")
        raise FileNotFoundError(f"The path does not exist: '{path}'")
    
    with open(OMNIDISC) as f:
        # Temporarily raise the recursion limit to insufferably high
        
        o = cast(dict, json5_load(f))
        id_list = (
            [f"{DATA.our_namespace}:{spec.id}" for spec in DATA.discs_index] + 
            [f"minecraft:{i}" for i in DATA.vanilla_discs]
        )
        if o.get(f"custom_metadata.{DATA.our_namespace}.id_list", []) != id_list:
            with open(ROOT / "data/omnidisc.json", "w") as f:
                json5_dump(
                    create_omnidisc_model(), f,
                    quote_keys = True, trailing_commas = False,
                    allow_duplicate_keys = True
                )
    
    MISSING_DISC = DiscSpec(
        parent = DATA, id = "missing", display_name = "Missing-Disc-Data", length = 1
    )
    Constants._init()

def deinit(path: Path):
    if DATA.dirty:
        logger.info("DATA is dirty, overriding data JSON file.")
        s = json5_dumps(
            DATA, cls = DataJSONEncoder,
            indent = 4, quote_style = QuoteStyle.PREFER_DOUBLE
        )
        with open(path, "w") as f:
            f.write(s)

@dataclass(frozen = True, unsafe_hash = True, kw_only = True)
class Data:
    mode: Literal["debug", "release"] = "debug"
    paths: PackSpecificField[Path, Path, Path] = field(default = None, init = False, metadata = {"serialize": False})
    common_version: int
    specific_version: PackSpecificField[int, int, None]
    vanilla_discs: list[str]
    discs_index: list[DiscSpec]
    pack_format: PackSpecificField[tuple[int, int], tuple[int, int], tuple[int, int]]
    our_namespace: str
    predicates: PredScoreboardContainer
    scoreboard_objectives: PredScoreboardContainer
    respackopts: RespackoptsData
    pack_cover: PackSpecificField[DiscID, DiscID, DiscID]
    recipes: dict[str, dict]
    add_tomes: bool = True
    tomes_index: list[Tome]
    tome_xp_color_index: list[str]
    critical_errors: list = field(
        default_factory = lambda: [],
        init = False,
        metadata = {"serialize": False}
    )
    
    dirty: bool = field(
        default = False,
        init = False,
        metadata = {"serialize": False}
    )
    
    def __post_init__(self):
        # File paths
        _p = None
        debug_paths_file_path = ROOT / "data/_debug_paths.json5"
        if self.mode == "debug":
            logger.debug("Debug mode detected, checking for debug paths...")
            if debug_paths_file_path.exists():
                with open(debug_paths_file_path) as f:
                    try:
                        _p = PackSpecificField(**{k: Path(v) for k, v in json5_load(f).items()})
                    except JSONDecodeError:
                        logger.error("%s contains malformed JSON5. Fallback to '/dist/unextracted'", debug_paths_file_path)
            else:
                logger.warning("%s does not exist. Fallback to /dist/unextracted", debug_paths_file_path)
        else:
            logger.debug("Release mode detected, setting paths...")
        forcesetattr(
            self, "paths",
            _p if _p is not None else PackSpecificField(
                datapack = ROOT / "dist/unextracted/datapack",
                respack = ROOT / "dist/unextracted/respack",
                soundpack = ROOT / "dist/unextracted/soundpack"
            )
        )
        for path in [self.paths.datapack, self.paths.respack]:
            try:
                path.mkdir(parents = True, exist_ok = True)
            except OSError:
                logger.exception(
                    "Can't create '%s' as a folder for some reason (exception below). I kindly ask you to go "
                    "there and fix it yourself. I don't want to handle an edge case where one of the parents "
                    "is a file. I have a life.", path
                )
                raise
        
        original_discs_index = [DiscSpec(parent = self, **i) for i in cast(list[dict], self.discs_index)]
        forcesetattr(self, "discs_index", list(filter(None, original_discs_index)))
        if len(original_discs_index) != len(self.discs_index):
            self.dirty = True
        
        # Check for duplicated IDs
        ids: dict[DiscID, list[int]] = {}
        rpo_ids: dict[str, list[int]] = {}
        for i, spec in enumerate(self.discs_index):
            if spec.id in ids:
                logger.critical("Found duplicated ID '%s' at indices %s", spec.id, ids[spec.id])
            ids[spec.id] = ids.get(spec.id, []) + [i]
            
            
            if spec.rpo_id in rpo_ids:
                logger.critical("Found duplicated config ID '%s' at indices %s", spec.rpo_id, rpo_ids[spec.rpo_id])
            rpo_ids[spec.rpo_id] = rpo_ids.get(spec.rpo_id, []) + [i]
        
        if any(len(i) > 1 for i in ids.values()):
            self.critical_errors.append(
                "\n".join(f"Disc ID '{id}' found in indices {", ".join(ls)}" for id, ls in ids.items() if len(ls) > 1)
            )
        if any(len(i) > 1 for i in rpo_ids.values()):
            self.critical_errors.append(
                "\n".join(f"Disc RPO ID '{id}' found in indices {", ".join(ls)}" for id, ls in rpo_ids.items() if len(ls) > 1)
            )
        
        forcesetattr(self, "predicates", PredScoreboardContainer(**self.predicates))
        forcesetattr(self, "scoreboard_objectives", PredScoreboardContainer(**self.scoreboard_objectives))
        forcesetattr(self, "pack_format", PackSpecificField(**self.pack_format))
        forcesetattr(self, "pack_cover", PackSpecificField(**self.pack_cover))
        forcesetattr(self, "specific_version", PackSpecificField(**self.specific_version))
        forcesetattr(self, "respackopts", RespackoptsData(**self.respackopts))
        forcesetattr(self, "tomes_index", [Tome(**i) for i in self.tomes_index])
        # They use the same pack format version
        forcesetattr(self.pack_format, "soundpack", self.pack_format.respack)
    
    def find_disc_spec(self, id: DiscID):
        for i in self.discs_index:
            if i.id == id: return i
        raise ValueError(f"No disc spec has the ID '{id}'")
    
    def datapack_version(self) -> str:
        return f"{self.common_version}.{self.specific_version.datapack}"
    
    def respack_version(self) -> str:
            return f"{self.common_version}.{self.specific_version.respack}"
    
    def version_check_key(self, version = None):
        return f"{self.our_namespace}.version_check.{self.common_version if version is None else version}"
    
    def respack_version_key(self) -> str:
        return f"{self.our_namespace}.respack_version"

@dataclass(frozen = True, unsafe_hash = True, kw_only = True)
class DiscSpec:
    COMMON_MUSIC_DIR: ClassVar[Path] = ROOT / "assets/music"
    COMMON_TEXTURE_DIR: ClassVar[Path] = ROOT / "assets/textures"
    
    parent: Data = field(
        repr = False, hash = False, metadata = {"serialize": False}
    )
    
    id: DiscID
    rpo_id: str = None
    display_name: str
    length: float = None
    range: int = 64
    comparator_output: int = 7
    texture_variation_display_name: str = "Default"
    display_name_variation_display_name: str = "Default"
    lore: tuple = field(default_factory = lambda: ())
    mcmeta: dict = field(default_factory = lambda: {}, hash = False)
    display_name_alts: tuple[DiscNameAlts, ...] = field(default_factory = lambda: ())
    texture_alts: tuple[DiscTextureAlts, ...] = field(default_factory = lambda: ())
    
    valid: bool = field(
        default = True,
        init = False,
        metadata = {"serialize": False}
    )
    
    def __bool__(self):
        return self.valid
    
    def __post_init__(self):
        forcesetattr(self, "sound_path", DiscSpec.COMMON_MUSIC_DIR / f"dist/{self.id}.ogg")
        self.sound_path: Path
        if self.id != "missing" and not self.sound_path.exists():
            logger.error(
                f"The music file for {self.id}, {self.sound_path.relative_to(self.COMMON_MUSIC_DIR)} does not exist. "
                "The music disc will play no music when used."
            )
        
        # Replacing config
        if self.rpo_id is None:
            forcesetattr(self, "rpo_id", to_camel_case(self.id))
        forcesetattr(self, "display_name_alts", tuple(DiscNameAlts(parent = self, **i) for i in self.display_name_alts))
        forcesetattr(self, "texture_alts", tuple(DiscTextureAlts(parent = self, **i) for i in self.texture_alts))
        forcesetattr(self, "lore", tuple(i for i in self.lore))
        if self.length == None:
            logger.warning(f"Disc {self.id} does not specify a length. Attempting to synthesize...")
            if not self.sound_path.exists():
                logger.error(f"Disc {self.id} does not have a length nor a valid music file. Setting length to '1'...")
                forcesetattr(self, "length", 1.0)
            forcesetattr(self, "length", cast(AudioSegment, AudioSegment.from_ogg(self.sound_path)).duration_seconds)
            forcesetattr(self.parent, "dirty", True)
            logger.debug("Found length of disc with ID '%s' being '%d'", self.id, self.length)
    
    @cache
    def stripped_display_name(self):
        s = self.display_name
        for code in FORMATTING_LIST.keys():
            s = s.replace(f"§{code}", "")
        return s
    
    def format_length(self):
        return f"{int(self.length // 60)}:{round(self.length % 60, 2)}"
    
    def subtitle_key(self) -> str:
        return f"{DATA.our_namespace}.display.{self.id}.subtitle"
    
    def ui_key(self) -> str:
        return f"{DATA.our_namespace}.display.{self.id}.ui"
    
    def lore_key(self):
        return f"{Constants.NAMESPACE}.display.{self.id}.lore"
    
    def rpo_redstone_tweaks_macro(self):
        return "${RTINFO%s}" % self.rpo_id
    
    @cache
    def display_name_for_subtitle(self, with_rpo_expansions: bool):
        if not with_rpo_expansions:
            return self.display_name
        s = self.display_name
        # Replace all formatting codes wih a macro
        for code, macro_part in FORMATTING_LIST.items():
            s = s.replace(f"§{code}", "${SB%s}" % macro_part)
        return s + self.rpo_redstone_tweaks_macro()

    @cache
    def display_name_for_ui(self, with_rpo_expansions: bool):
        if not with_rpo_expansions:
            return self.display_name
        s = self.display_name
        # Replace all formatting codes wih a macro
        for code, macro_part in FORMATTING_LIST.items():
            s = s.replace(f"§{code}", "${UI%s}" % macro_part)
        return s + " " + self.rpo_redstone_tweaks_macro()
    
    def sound_id(self) -> str:
        return f"{DATA.our_namespace}:music_disc.{self.id}"
    
    def rpo_option_key(self):
        return f"rpo.{DATA.respackopts.namespace}.{DATA.respackopts.config_namespace.texture_variation}.{self.rpo_id}"
    
    def display_name_in_mu_for_subtitles(self):
        return mu_ternary(
            mu_enum_equals(f"{DATA.respackopts.namespace}.{DATA.respackopts.config_namespace.misc}.formattingCodes", "enabled"),
            f"'{self.display_name}'", f"'{self.stripped_display_name()}'"
        )
    
    def display_name_in_mu_for_ui(self):
        return mu_ternary(
            mu_enum_nequals(f"{DATA.respackopts.namespace}.{DATA.respackopts.config_namespace.misc}.formattingCodes", "disabled"),
            f"'{self.display_name}'", f"'{self.stripped_display_name()}'"
        )

MISSING_DISC: DiscSpec

@dataclass(frozen = True, unsafe_hash = True, kw_only = True)
class RespackoptsData:
    namespace: str
    config_namespace: RespackoptsCategory
    config_display_name: RespackoptsCategory
    def __post_init__(self):
        forcesetattr(self, "config_namespace", RespackoptsCategory(**self.config_namespace))
        forcesetattr(self, "config_display_name", RespackoptsCategory(**self.config_display_name))

@dataclass(frozen = True, unsafe_hash = True, kw_only = True)
class RespackoptsCategory:
    misc: str
    display_name_variation: str
    texture_variation: str
    xp_tomes: str

@dataclass(frozen = True, unsafe_hash = True, kw_only = True)
class DiscNameAlts:
    parent: DiscSpec = field(hash = False, metadata = {"serialize": False})
    variation_id: str
    variation_display_name: str
    display_name: str
    
    @cache
    def stripped_display_name(self):
        s = self.display_name
        for code in FORMATTING_LIST.keys():
            s = s.replace(f"§{code}", "")
        return s
    
    def rpo_option_key(self):
            return f"rpo.{DATA.respackopts.namespace}.{DATA.respackopts.config_namespace.display_name_variation}.{self.parent.rpo_id}.{self.variation_id}"
    
    def display_name_in_mu_for_subtitles(self):
            return mu_ternary(
                mu_enum_equals(f"{DATA.respackopts.namespace}.{DATA.respackopts.config_namespace.misc}.formattingCodes", "enabled"),
                f"'{self.display_name}'", f"'{self.stripped_display_name()}'"
            )
        
    def display_name_in_mu_for_ui(self):
        return mu_ternary(
            mu_enum_nequals(f"{DATA.respackopts.namespace}.{DATA.respackopts.config_namespace.misc}.formattingCodes", "disabled"),
            f"'{self.display_name}'", f"'{self.stripped_display_name()}'"
        )

@dataclass(frozen = True, unsafe_hash = True, kw_only = True)
class DiscTextureAlts:
    parent: DiscSpec = field(hash = False, metadata = {"serialize": False})
    variation_id: str
    variation_display_name: str
    mcmeta: dict = field(default_factory = lambda: {}, hash = False)
    def rpo_option_key(self):
        return f"rpo.{DATA.respackopts.namespace}.{DATA.respackopts.config_namespace.texture_variation}.{self.parent.rpo_id}.{self.variation_id}"

@dataclass(frozen = True, unsafe_hash = True, kw_only = True)
class PackSpecificField[DatapackT, RespackT, SoundpackT]:
    datapack: DatapackT = None
    respack: RespackT = None
    soundpack: SoundpackT = field(default=None, metadata={"serialize": False})

@dataclass(frozen = True, unsafe_hash = True, kw_only = True)
class PredScoreboardContainer:
    trigger_disc_ui: str
    trigger_tome_config_ui: str
    select_disc: str
    restore_disc: str
    pack_info: str
    configure_xp_tomes: str
    
    def __iter__(self):
        yield self.trigger_disc_ui
        yield self.trigger_tome_config_ui
        yield self.select_disc
        yield self.restore_disc
        yield self.pack_info
        yield self.configure_xp_tomes

@dataclass(frozen=True, unsafe_hash=True, kw_only=True)
class Tome:
    id: str
    display_name: str
    recipe_key: dict[str, str]
    recipe_pattern: tuple[str, str, str]
    max_xp_levels: InitVar[int] = None
    max_xp: int = None
    default_xp_color: str
    retrieve_until_next_level: bool = True
    store_until_previous_level: bool = False
    retrieve_xp_orbs: bool = True
    lock: tuple = ()
    
    def __post_init__(self, max_xp_levels: int | None):
        if max_xp_levels is not None:
            forcesetattr(self, "max_xp", xp_levels_to_points(max_xp_levels))
        forcesetattr(self, "lock", tuple(self.lock))
    
    def recipe_json_path(self):
        return Constants.DATAPACK_PATH / f"data/{Constants.NAMESPACE}/recipe/{self.id}.json"

class ConstantsMeta(type):
    _lock: bool = False
    def __setattr__(cls, name, value):
        if cls._lock:
            raise FrozenInstanceError(f"'{cls.__name__}' is not intended to be modified")
        return super().__setattr__(name, value)
    
    def __delattr__(cls, name, value):
        if cls._lock:
            raise FrozenInstanceError(f"'{cls.__name__}' is not intended to be modified")
        return super().__delattr__(name, value)

class Constants(metaclass = ConstantsMeta):
    DATAPACK_PATH: Final[Path]
    RESPACK_PATH: Final[Path]
    NAMESPACE: Final[str]
    
    @classmethod
    def _init(cls):
        cls.DATAPACK_PATH = Path(DATA.paths.datapack)
        cls.RESPACK_PATH = Path(DATA.paths.respack)
        cls.NAMESPACE = DATA.our_namespace
        cls._lock = True
    
    disc_selection: Final = "disc_selection"
    apply_disc: Final = "apply_disc"
    restore_disc: Final = "restore_disc"
    load: Final = "load"
    tick: Final = "tick"
    info: Final = "info"
    is_holding_disc: Final = "is_holding_disc"
    configure_xp_tome: Final = "configure_xp_tome"
    
    @classproperty
    def disc_selection_dialog(cls):
        return f"{cls.NAMESPACE}:{cls.disc_selection}"
    
    @classproperty
    def configure_xp_tome_dialog(cls):
        return f"{cls.NAMESPACE}:{cls.configure_xp_tome}"
    
    @classproperty
    def apply_disc_fn(cls) -> str:
        return f"{cls.NAMESPACE}:{cls.apply_disc}"
    
    @classproperty
    def restore_disc_fn(cls) -> str:
        return f"{cls.NAMESPACE}:{cls.restore_disc}"
    
    @classproperty
    def load_fn(cls) -> str:
        return f"{cls.NAMESPACE}:{cls.load}"
    
    @classproperty
    def tick_fn(cls) -> str:
        return f"{cls.NAMESPACE}:{cls.tick}"
    
    @classproperty
    def info_fn(cls):
        return f"{cls.NAMESPACE}:{cls.info}"
    
    @classproperty
    def is_holding_disc_fn(cls):
        return f"{cls.NAMESPACE}:{cls.is_holding_disc}"
    
    @classproperty
    def configure_xp_tome_fn(cls):
        return f"{cls.NAMESPACE}:{cls.configure_xp_tome}"
    
    @classproperty
    def disc_selection_dialog_path(cls):
        return cls.DATAPACK_PATH / f"data/{cls.NAMESPACE}/dialog/{cls.disc_selection}.json"
    
    @classproperty
    def configure_xp_tome_dialog_path(cls):
        return cls.DATAPACK_PATH / f"data/{cls.NAMESPACE}/dialog/{cls.configure_xp_tome}.json"
    
    @classproperty
    def load_fn_path(cls):
        return cls.DATAPACK_PATH / f"data/{cls.NAMESPACE}/function/{cls.load}.mcfunction"
    
    @classproperty
    def tick_fn_path(cls):
        return cls.DATAPACK_PATH / f"data/{cls.NAMESPACE}/function/{cls.tick}.mcfunction"
    
    @classproperty
    def apply_disc_fn_path(cls):
        return cls.DATAPACK_PATH / f"data/{cls.NAMESPACE}/function/{cls.apply_disc}.mcfunction"
    
    @classproperty
    def restore_disc_fn_path(cls):
        return cls.DATAPACK_PATH / f"data/{cls.NAMESPACE}/function/{cls.restore_disc}.mcfunction"
    
    @classproperty
    def info_fn_path(cls):
        return cls.DATAPACK_PATH / f"data/{cls.NAMESPACE}/function/{cls.info}.mcfunction"
    
    @classproperty
    def is_holding_disc_fn_path(cls):
        return cls.DATAPACK_PATH / f"data/{cls.NAMESPACE}/function/{cls.is_holding_disc}.mcfunction"
    
    @classproperty
    def quick_actions_dialog_tag_path(cls):
        return cls.DATAPACK_PATH / "data/minecraft/tags/dialog/quick_actions.json"
    
    @classproperty
    def pause_screen_additions_dialog_tag_path(cls):
        return cls.DATAPACK_PATH / "data/minecraft/tags/dialog/pause_screen_additions.json"
    
    @classproperty
    def load_fn_tag_path(cls):
        return cls.DATAPACK_PATH / "data/minecraft/tags/function/load.json"
    
    @classproperty
    def tick_fn_tag_path(cls):
        return cls.DATAPACK_PATH / "data/minecraft/tags/function/tick.json"
    
    @classproperty
    def configure_xp_tome_fn_path(cls):
        return cls.DATAPACK_PATH / f"data/{cls.NAMESPACE}/function/{cls.configure_xp_tome}.mcfunction"

# TODO: Clean up needed
def xp_levels_to_points(i: int) -> int:
    assert i >= 0
    if i == 0:
        return 0
    elif 0 < i <= 15:
        return xp_levels_to_points(i - 1) + 2*(i-1) + 7
    elif i <= 30:
        return xp_levels_to_points(i - 1) + 5*(i-1) - 38
    return xp_levels_to_points(i - 1) + 9*(i-1) - 158

# def create_omnidisc_model() -> dict:
#     def _branch(head=None, *rest) -> dict:
#         if head == None:
#             return {
#                 "type": "model",
#                 "model": f"{DATA.our_namespace}:missing"
#             }
#         return {
#             "type": "condition",
#             "property": "component",
#             "predicate": "jukebox_playable",
#             "value": {
#                 "song": head[0]
#             },
#             "on_true": {
#                 "type": "model",
#                 "model": head[1]
#             },
#             "on_false": _branch(*rest)
#         }
        
#     return {
#         f"custom_metadata.{DATA.our_namespace}.id_list": (
#             [f"{DATA.our_namespace}:{spec.id}" for spec in DATA.discs_index] + 
#             [f"minecraft:{i}" for i in DATA.vanilla_discs]
#         ),
#         "model": _branch(
#             *(
#                 [(i, f"item/music_disc_{i}") for i in DATA.vanilla_discs] +
#                 [(f"{DATA.our_namespace}:{spec.id}", f"{DATA.our_namespace}:item/{spec.id}")
#                     for spec in DATA.discs_index]
#             )
#         )
#     }

def create_omnidisc_model() -> dict:
    return {
        f"custom_metadata.{DATA.our_namespace}.id_list": (
            [f"{DATA.our_namespace}:{spec.id}" for spec in DATA.discs_index] + 
            [f"minecraft:{i}" for i in DATA.vanilla_discs]
        ),
        "model": {
            "type": "select",
            "property": "component",
            "component": "jukebox_playable",
            "cases": [
                {
                    "when": f"minecraft:{disc}",
                    "model": {
                        "type": "model",
                        "model": f"minecraft:item/music_disc_{disc}"
                    }
                } for disc in DATA.vanilla_discs
            ] + [
                {
                    "when": f"{DATA.our_namespace}:{spec.id}",
                    "model": {
                        "type": "model",
                        "model": f"{DATA.our_namespace}:item/{spec.id}"
                    }
                } for spec in DATA.discs_index
            ]
        }
    }

if __name__ == "__main__":
    raise Exception("Run the wrong file dumbass")