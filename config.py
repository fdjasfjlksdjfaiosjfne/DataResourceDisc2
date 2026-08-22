from pathlib import Path
import typing
import json

def to_camel_case(s: str) -> str:
    parts = s.replace("-", "_").split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])

class Config:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_dct: dict | None = None):
        p = Path(__file__).parent
        if getattr(self, "_dct", None) is None:
            self._dct = config_dct
            
            if self.is_debug_mode():
                with open(p / "_test_path.json") as f:
                    o = json.dump(f)
                    self._datapack_path = o["datapack"]
                    self._respack_path = o["respack"]
                    self._soundpack_path = o["soundpack"]
            else:
                self._datapack_path = p / "dist/unextracted/datapack"
                self._respack_path = p / "dist/unextracted/respack"
                self._soundpack_path = p / "dist/unextracted/soundpack"
    
    def __getitem__(self, key):
        return self._dct[key]
    
    def is_debug_mode(self) -> bool: return self["mode"] == "debug"
    def is_release_mode(self) -> bool: return self["mode"] == "release"
    def our_namespace(self) -> str: return self["our_namespace"]
    def disc_index(self) -> list[DiscSpec]: return [DiscSpec(**i) for i in self["discs_index"]]
    def debug_datapack_path(self) -> Path: return self._datapack_path
    def debug_respack_path(self) -> Path: return self._respack_path
    def debug_soundpack_path(self) -> Path: return self._soundpack_path
    def datapack_pack_format(self) -> tuple[int, int]: return tuple(self["pack_format"]["datapack"])
    def respack_pack_format(self) -> tuple[int, int]: return tuple(self["pack_format"]["respack"])
    def version(self) -> int: return self["version"]
    def vanilla_discs(self) -> list[str]: return self["vanilla_discs"]
    def objective(self, s: typing.Literal["pack_info", "trigger_ui", "select_disc"]) -> str: 
        return self["names"]["scoreboard_objective"][s]
    def respackopts_namespace(self) -> str:
        return self["respackopts"]["namespace"]
    def predicate(self, s: typing.Literal["pack_info", "trigger_ui", "select_disc"], with_namespace: bool = True) -> str: 
        return (f"{self.our_namespace()}:" if with_namespace else "") + self["names"]["predicate"][s]
    def datapack_pack_png_id(self) -> str:
        return self["pack_png"]["datapack"]
    def respack_pack_png_id(self) -> str:
            return self["pack_png"]["respack"]
    def soundpack_pack_png_id(self) -> str: 
        return self["pack_png"]["soundpack"]


class DiscSpec:
    @classmethod
    def missing(cls) -> "DiscSpec":
        return cls(f'missing', 0, "???")
    
    def __init__(self, 
                 id, display, length: float, range = 64,
                 comparator_output = 7, alts: list[dict] | None = None, 
                 variation_display: str = "Default", mcmeta: dict | None = None, 
                 config_id: str | None = None, **kwargs):
        self.id: str = id
        self.config_id: str = to_camel_case(self.id) if config_id is None else config_id
        self.display: str = display
        self.length: float = length
        self.range: int = range
        self.alts = [DiscAppearance(**i) for i in alts] if alts is not None else []
        self.variation_display = variation_display
        self.mcmeta = mcmeta
        self.comparator_output: int = comparator_output
    
    def format_length(self):
        return f"{int(self.length // 60)}:{round(self.length % 60, 2)}"
    
    def has_alts(self) -> bool:
        return len(self.alts) != 0

class DiscAppearance:
    def __init__(self, variation_id: str, display: str, mcmeta: dict | None = None, **kwargs):
        self.variation_id = variation_id
        self.display = display
        self.mcmeta = mcmeta