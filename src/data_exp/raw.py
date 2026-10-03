"""Contains pure, unfiltered, raw data. Well, most of it."""

from typing import Final, Literal, NewType

from .discs import ThroughPatchesOfViolet, WellRested

NS = "custom_discs"
Mode: Final[Literal["debug", "release"]] = "debug"

VanillaDiscs: Final = [
    "11",
    "13",
    "cat",
    "5",
    "stal",
    "mellohi",
    "pigstep",
    "otherside",
    "bounce",
    "blocks",
    "chirp",
    "far",
    "mall",
    "ward",
    "wait",
    "relic",
    "precipice",
    "creator",
    "tears",
    "creator_music_box",
    "lava_chicken",
]

# ^ Scoreboard objectives
ScoreboardObjective = NewType("ScoreboardObjective", str)
TriggerDiscUIObj: Final[ScoreboardObjective] = "open_disc_ui"
TriggerTomeConfigUiObj: Final[ScoreboardObjective] = "open_tome_ui"
SelectDiscObj: Final[ScoreboardObjective] = "select_disc"
RestoreDiscObj: Final[ScoreboardObjective] = "restore_disc"
PackInfoObj: Final[ScoreboardObjective] = "disc_pack_info"
ConfigureXPTomesObj: Final[ScoreboardObjective] = "configure_xp_tomes"
# ^ Predicates
Predicate = NewType("Predicate", str)
TriggerDiscUIPredName: Final = "request_disc_ui"
TriggerTomeConfigUiPredName: Final = "request_tome_ui"
SelectDiscPredName: Final = "request_select_disc"
RestoreDiscPredName: Final = "request_restore_disc"
PackInfoPredName: Final = "request_pack_info"
ConfigureXPTomesPredName: Final = "request_configure_xp_tomes"

TriggerDiscUIPred: Final[Predicate] = f"{NS}:{TriggerDiscUIPredName}"
TriggerTomeConfigUiPred: Final[Predicate] = f"{NS}:{TriggerTomeConfigUiPredName}"
SelectDiscPred: Final[Predicate] = f"{NS}:{SelectDiscPredName}"
PackInfoPred: Final[Predicate] = f"{NS}:{PackInfoPredName}"
ConfigureXPTomesPred: Final[Predicate] = f"{NS}:{ConfigureXPTomesPredName}"
# ^ Respackopts
RPONS: Final = "customMusicDiscs"

MiscConfigNS: Final = "misc"
DisplayNameVariationConfigNS: Final = "display_name_variation"
TextureVariationConfigNS: Final = "texture_variation"
XPTomesConfigNS: Final = "xp_tomes"

MiscConfigDisplayName: Final = "Miscellaneous"
DisplayNameVariationConfigDisplayName: Final = "Display Names"
TextureVariationConfigDisplayName: Final = "Textures"
XPTomesConfigDisplayName: Final = "XP Tomes"
# ^ Functions
InfoFnName: Final = "info"
LoadFnName: Final = "load"
TickFnName: Final = "tick"
ApplyDiscName: Final = "apply_disc"
RestoreDiscName: Final = "restore_disc"
ConfigureXPTomeName: Final = "..."
# ^ Pack Information
DatapackFormat: Final = (121, 0)
RespackFormat: Final = (97, 1)
DatapackFormat: Final = WellRested.id
RespackFormat: Final = ThroughPatchesOfViolet.id