from dataclasses import dataclass
from typing import Literal, cast, TYPE_CHECKING, ClassVar
from pathlib import Path
from logging import getLogger
from pydub import AudioSegment

ROOT = Path(__file__).parent.parent
logger = getLogger(__name__)


def to_camel_case(s: str) -> str:
    parts = s.replace("-", "_").split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])

def init():
    pass

DATA: Data = cast(Data, None)

@dataclass
class Data:
    mode: Literal["debug", "release"] = "debug"
    common_version: int
    respack_version: int = 0
    vanilla_discs: list[str]
    discs_index: list[DiscSpec]
    pack_format: PackSpecificField[tuple[int, int], tuple[int, int], tuple[int, int]]
    names: dict
    predicates: PredScoreboardContainer
    scoreboard_objectives: PredScoreboardContainer
    our_namespace: str
    respackopts_namespace: str
    pack_cover: PackSpecificField[str, str, str]
    
    def __post_init__(self):
        self.discs_index = list(filter(DiscSpec(**i) for i in cast(list[dict], self.discs_index)))
        DATA = self if DATA is None else DATA
        self.predicates = PredScoreboardContainer(**self.names["predicate"])
        self.scoreboard_objectives = PredScoreboardContainer(**self.names["scoreboard_objective"])
        # They use the same thing
        self.pack_format.soundpack = self.pack_format.respack

@dataclass
class DiscSpec:
    COMMON_MUSIC_DIR: ClassVar[Path] = ROOT / "assets/music"
    COMMON_TEXTURE_DIR: ClassVar[Path] = ROOT / "assets/textures"
    
    id: str
    config_id: str = None
    display_name: str
    length: float = None
    range: int = 64
    comparator_output: int = 7
    variation_display_name: str = "Default"
    mcmeta: dict
    spec_alts: list[DiscAlts]
    
    valid: bool = True
    
    def __bool__(self):
        return self.valid
    
    def __post_init__(self):
        self.sound_path: Path = DiscSpec.COMMON_MUSIC_DIR / f"dist/{self.id}.ogg"
        if not self.sound_path.exists():
            logger.error(
                f"The music file for {self.id}, {self.sound_path.relative_to(self.COMMON_MUSIC_DIR)} does not exist. "
                "The music disc will play no music when used."
            )
        
        # Replacing config
        if self.config_id is None:
            self.config_id = to_camel_case(self.id)
        self.spec_alts = [DiscAlts(parent = self, **i) for i in self.spec_alts]
        if self.length == None:
            logger.warning(f"Disc {self.id} does not specify a length. Attempting to synthesize...")
            if not self.sound_path.exists():
                logger.error(f"Disc {self.id} does not have a length nor a valid music file. Setting length to '1'...")
                self.length = 1.0
            self.length = cast(AudioSegment, AudioSegment.from_ogg(self.sound_path)).duration_seconds

@dataclass
class DiscAlts:
    parent: DiscSpec
    variation_id: str
    variation_display_name: str
    mcmeta: dict

@dataclass
class PackSpecificField[DatapackT, RespackT, SoundpackT]:
    datapack: DatapackT
    respack: RespackT
    soundpack: SoundpackT

@dataclass
class PredScoreboardContainer:
    trigger_ui: str
    select_disc: str
    pack_info: str