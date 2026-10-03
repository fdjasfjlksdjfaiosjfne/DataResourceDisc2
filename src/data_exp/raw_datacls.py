"""A submodule containing dataclasses for the raw dataclasses
"""

from abc import ABC
from dataclasses import InitVar, dataclass, field, fields
from typing import NewType
from ..core import to_camel_case

DiscID = NewType("DiscID", str)

class RawBaseDataclass(ABC):
    _dirty = field(init = False, default = False, hash = False, metadata = {"serialize": False})
    "The base class for all raw dataclass. Provides `__post_init__` and `is_dirty`"
    def __post_init__(self):
        for field in fields(self):
            raw = getattr(self, field.name)
            if "raw_verification" in field.metadata:
                if field.metadata["raw_verification"](raw):
                    object.__setattr__(self, "_dirty", True)
            if "post_processing" in field.metadata:
                object.__setattr__(
                    self, field.name, 
                    field.metadata["post_processing"](raw, self)
                )
            if "verification" in field.metadata:
                if field.metadata["verification"](getattr(self, field.name)):
                    object.__setattr__(self, "_dirty", True)
    
    def is_dirty(self):
        if self._dirty:
            return True
        return any(getattr(getattr(self, field.name), "is_dirty", lambda: False)() for field in fields(self))

@dataclass(frozen = True, kw_only = True)
class Data(RawBaseDataclass):
    common_version: int
    specific_version: PackSpecificField[int, int] = field(
        metadata = {"post_processing": lambda o, _: PackSpecificField(**o)}
    )
    vanilla_discs: list[int]
    discs_index: list[DiscSpec] = field(
        metadata = {"post_processing": lambda o, _: list(DiscSpec(**i) for i in o)}
    )
    pack_format: PackSpecificField[tuple[int, int], tuple[int, int]] = field(
        metadata = {"post_processing": lambda o, _: PackSpecificField(**{k: tuple(v) for k, v in o})}
    )
    our_namespace: str
    predicates: ScoreObjectives = field(
        metadata = {"post_processing": lambda o, _: PackSpecificField(**o)}
    )
    scoreboard_objectives: ScoreObjectives = field(
        metadata = {"post_processing": lambda o, _: PackSpecificField(**o)}
    )
    respackopts: RespackoptsData = field(
        metadata = {"post_processing": lambda o, _: RespackoptsData(**o)}
    )
    pack_cover: PackSpecificField[DiscID, DiscID] = field(
        metadata = {"post_processing": lambda o, _: PackSpecificField(**o)}
    )
    recipes: dict[str, dict]
    add_tomes: bool = True
    tomes_index: list[Tome] = field(
        metadata = {"post_processing": lambda o, _: list(Tome(**i) for i in o)}
    )
    tome_xp_color_index: list[str]

@dataclass(frozen = True, kw_only = True)
class DiscSpec(RawBaseDataclass):
    id: DiscID
    rpo_id: str = field(
        default = None,
        metadata = {
            "post_processing": lambda o, self: (
                o if o is not None else to_camel_case(self.id)
            )
        }
    )
    display_name: str
    length: float = field(
        default = None,
        metadata = {
            "post_processing": lambda o, self: (
                o if o is not None else self.calculate_length()
            )
        }
    )
    range: int = 64
    comparator_output: int = 7
    texture_variation_display_name: str = "Default"
    display_name_variation_display_name: str = "Default"
    lore: list = field(default_factory = lambda: [])
    mcmeta: dict = field(default_factory = lambda: {}, hash = False)
    display_name_alts: list[DiscNameAlts] = field(
        default_factory = lambda: [],
        metadata = {"post_processing": lambda o, self: lambda: [DiscNameAlts(parent = self, **i) for i in o]}
    )
    texture_alts: list[DiscTextureAlts] = field(
        default_factory = lambda: [],
        metadata = {"post_processing": lambda o, self: lambda: [DiscTextureAlts(parent = self, **i) for i in o]}
    )
    def calculate_length(self):
        pass

@dataclass(frozen = True, kw_only = True)
class DiscNameAlts:
    parent: DiscSpec = field(hash = False, metadata = {"serialize": False})
    variation_id: str
    variation_display_name: str
    display_name: str

@dataclass(frozen = True, kw_only = True)
class DiscTextureAlts:
    parent: DiscSpec = field(hash = False, metadata = {"serialize": False})
    variation_id: str
    variation_display_name: str
    mcmeta: dict = field(default_factory = lambda: {}, hash = False)

@dataclass(frozen = True, kw_only = True)
class ScoreObjectives(RawBaseDataclass):
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

@dataclass(frozen = True, kw_only = True)
class RespackoptsData:
    namespace: str
    config_namespace: RespackoptsCategory = field(
        metadata = {"post_processing": lambda o, _: RespackoptsCategory(**o)}
    )
    config_display_name: RespackoptsCategory = field(
        metadata = {"post_processing": lambda o, _: RespackoptsCategory(**o)}
    )

@dataclass(frozen = True, unsafe_hash = True, kw_only = True)
class RespackoptsCategory(RawBaseDataclass):
    misc: str
    display_name_variation: str
    texture_variation: str
    xp_tomes: str

@dataclass(frozen = True, kw_only = True)
class Tome(RawBaseDataclass):
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
    lock: list = field(default_factory = lambda: [])

@dataclass(frozen = True, kw_only = True)
class PackSpecificField[DatapackT, RespackT](RawBaseDataclass):
    datapack: DatapackT
    respack: RespackT
