from pathlib import Path
from typing import Callable
from config import Config, DiscSpec
import json
try:
    import json5
except ImportError:
    json5 = json
import shutil

config = Config()

COMPARATOR = "§f\ue101§7"
CLOCK = "§f\ue102§7"

def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding = "utf-8")

def init():
    root = config.debug_respack_path()
    init_sound_pack()
    
    for path in root.iterdir():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    
    
    ASSET_PATH = root / "assets"
    OUR_NAMESPACE = ASSET_PATH / config.our_namespace()
    MINECRAFT_NAMESPACE = ASSET_PATH / "minecraft"
    ITEM_TEXTURES = OUR_NAMESPACE / "textures" / "item"
    
    copy_item_textures(ITEM_TEXTURES, config, root)

    udc = json.dumps(create_ultimatum_disc_chooser())
    GENERATED_TEXT_FILES = {
        # Item model supporting RPO
        OUR_NAMESPACE / f"models_rpo/item/{spec.id}.json": item_model_json(spec, with_rpo = True)
        for spec in config.disc_index() + [DiscSpec.missing()]
    } | {
        # Item model RPO
        OUR_NAMESPACE / f"models_rpo/item/{spec.id}.json.rpo": item_model_json_rpo(spec)
        for spec in config.disc_index() if spec.has_alts()
    } | {
        # Item model without RPO
        OUR_NAMESPACE / f"models/item/{spec.id}.json": item_model_json(spec, with_rpo = False)
        for spec in config.disc_index() + [DiscSpec.missing()]
    } | {
        MINECRAFT_NAMESPACE / f"items/music_disc_{i}.json": lambda: udc
        for i in config.vanilla_discs()
    } | {
        OUR_NAMESPACE / f"models/.rpo": lambda: json.dumps({"condition": "false", "fallback": [f"{config.our_namespace()}:lang_rpo"]}),
        MINECRAFT_NAMESPACE / "lang_rpo/en_us.json": us_english_json(with_rpo = True),
        MINECRAFT_NAMESPACE / "lang_rpo/en_us.json.rpo": lang_json_rpo,
        MINECRAFT_NAMESPACE / "lang/en_us.json": us_english_json(with_rpo = False),
        MINECRAFT_NAMESPACE / "lang/.rpo": lambda: json.dumps({"condition": "false", "fallback": [f"{config.our_namespace()}:lang_rpo"]}),
        root / "respackopts.json5": respackopts_json,
        root / "pack.mcmeta": pack_mcmeta(False)
    }
    
    for path, generator in GENERATED_TEXT_FILES.items():
        print(f"Writing {path.relative_to(root)}...")
        write_file(path, generator())
    
    print(f"Copying pack.png for the resource pack...")
    (Path(__file__).parent / f"textures/{config.respack_pack_png_id()}.png").copy(root / "pack.png")

def init_sound_pack():
    root = config.debug_soundpack_path()
    
    for path in root.iterdir():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    
    write_file(root / "pack.mcmeta", pack_mcmeta(True)())
    SOUNDS = root / f"assets/{config.our_namespace()}/sounds"
    write_file(root / f"assets/{config.our_namespace()}/sounds.json", sounds_json())
    copy_sounds(SOUNDS, config, root)
    (Path(__file__).parent / f"textures/{config.soundpack_pack_png_id()}.png").copy(root / "pack.png")

def pack_mcmeta(for_sound_files: bool):
    return lambda: json.dumps({
        "pack": {
            "min_format": config.respack_pack_format(),
            "max_format": config.respack_pack_format(),
            "description": f"[Ver {config.version()}] " + 
                ("Provides sounds and sound events for discs" if for_sound_files else "Provides textures for discs")
        }
    })

def item_model_json_rpo(spec: DiscSpec) -> Callable[[], str]:
    key = f"{config.respackopts_namespace()}.variations.{spec.config_id}"
    return lambda: json5.dumps({
        "expansions": {
            "variation": f"(('' || {key}) == 'default') ? '' : ('-' || {key})"
        }
    })

def item_model_json(spec: DiscSpec, with_rpo: bool) -> Callable[[], str]:
    return lambda: json.dumps({
        "parent": "item/generated",
        "textures": {
            "layer0": f"{config.our_namespace()}:item/{spec.id}" + ("${variation}" if with_rpo and spec.has_alts() else "")
        }
    })

def copy_item_textures(path: Path, config: Config, root: Path):
    original_texture_dir = Path(__file__).parent / "textures"
    for spec in config.disc_index() + [DiscSpec.missing()]:
        
        new_path = path / f"{spec.id}.png"
        print(f"Copying texture file to {new_path.relative_to(root)}...")
        
        png = original_texture_dir / f"{spec.id}.png"
        
        if (not png.exists()) or not png.is_file():
                print(f"\\e[0;91m{png.relative_to(Path(__file__).parent)} does not exist, using fallback\\e[0m")
                png = original_texture_dir / f"{DiscSpec.missing().id}.png"
        
        new_path.parent.mkdir(parents=True, exist_ok=True)
        png.copy(new_path)
        
        if spec.mcmeta is not None:
            write_file(path / f"{spec.id}.png.mcmeta", json.dumps(spec.mcmeta))
        
        for alt in spec.alts:
            new_path = path / f"{spec.id}-{alt.variation_id}.png"
            print(f"Copying texture file to {new_path.relative_to(root)}...")
            png = original_texture_dir / f"{spec.id}-{alt.variation_id}.png"
            
            if (not png.exists()) or not png.is_file():
                print(f"\\e[0;91m{png.relative_to(Path(__file__).parent)} does not exist, using fallback\\e[0m")
                png = original_texture_dir / f"{DiscSpec.missing().id}.png"
            
            new_path.parent.mkdir(parents=True, exist_ok=True)
            png.copy(new_path)
            
            if alt.mcmeta is not None:
                write_file(path / f"{spec.id}-{alt.variation_id}.png.mcmeta", json.dumps(alt.mcmeta))

def copy_sounds(path: Path, config: Config, root: Path):
    original_music_files = Path(__file__).parent / "music/dist"
    for spec in config.disc_index():
        new_path = path / f"{spec.id}.ogg"
        print(f"Copying music file to {new_path.relative_to(root)}...")
        original_ogg = original_music_files / f"{spec.id}.ogg"
        if (not original_ogg.exists()) or not original_ogg.is_file():
            print(f"\\e[0;91m{original_ogg.relative_to(Path(__file__).parent)} does not exist, skipping\\e[0m")
            continue
        new_path.parent.mkdir(parents=True, exist_ok=True)
        new_path.touch()
        original_ogg.copy(new_path)

def create_ultimatum_disc_chooser() -> dict:
    def _branch(head=None, *rest) -> dict:
        if head == None:
            return {
                "type": "model",
                "model": f"{config.our_namespace()}:missing"
            }
        return {
            "type": "condition",
            "property": "component",
            "predicate": "jukebox_playable",
            "value": {
                "song": head[0]
            },
            "on_true": {
                "type": "model",
                "model": head[1]
            },
            "on_false": _branch(*rest)
        }
        
    return {
        "model": _branch(
            *(
                [(i, f"item/music_disc_{i}") for i in config.vanilla_discs()] +
                [(f"{config.our_namespace()}:{spec.id}", f"{config.our_namespace()}:item/{spec.id}") 
                    for spec in config.disc_index()]
            )
        )
    }

def sounds_json() -> str:
    return json.dumps({
        f"music_disc.{spec.id}": {
            "sounds": [{
                "name": f"{config.our_namespace()}:{spec.id}",
                "stream": True
            }]
        } for spec in config.disc_index()
    })

def us_english_json(with_rpo: bool) -> Callable[[], str]:
    previous_updates = {
        f"{config.our_namespace()}.version_check.{i}": "Your resource pack should work fine!"
        for i in range(1, config.version())
    }
    
    disc_names_for_subtitle = {
        f"{config.our_namespace()}:display.{spec.id}.subtitle": efcisds(spec.display, spec.config_id) if with_rpo else spec.display
        for spec in config.disc_index()
    }
    
    disc_names_for_ui = {
        f"{config.our_namespace()}:display.{spec.id}.ui": efciuids(spec.display, spec.config_id) if with_rpo else spec.display
        for spec in config.disc_index()
    }
    
    echoes_of_logging = {
        
    }
    
    variation_opts = {}
    if with_rpo:
        for spec in config.disc_index():
            if len(spec.alts) != 0:
                variation_opts.update({
                    f"rpo.{config.respackopts_namespace()}.variations.{spec.config_id}.default": spec.variation_display,
                    f"rpo.{config.respackopts_namespace()}.variations.{spec.config_id}": spec.display
                } | {
                    f"rpo.{config.respackopts_namespace()}.variations.{spec.config_id}.{opt.variation_id}": opt.display
                    for opt in spec.alts
                })
    
    
    rpo_specific = {
        f"rpo.{config.respackopts_namespace()}": "Custom Music Discs",
        f"rpo.{config.respackopts_namespace()}.misc": "Misc",
        f"rpo.{config.respackopts_namespace()}.variations": "Variations",
        f"rpo.{config.respackopts_namespace()}.misc.formattingCodes": "Enable formatting codes",
        f"rpo.{config.respackopts_namespace()}.misc.formattingCodes.enabled": "§aEnabled§r",
        f"rpo.{config.respackopts_namespace()}.misc.formattingCodes.disabled": "§cDisabled§r",
        f"rpo.{config.respackopts_namespace()}.misc.formattingCodes.only_ui": "§eUI Only§r",
        f"rpo.{config.respackopts_namespace()}.misc.redstoneTweaksTooltip": "Redstone Tweaks-styled Tooltip",
        f"rpo.{config.respackopts_namespace()}.misc.redstoneTweaksTooltip.disabled": "§cDisabled§r",
        f"rpo.{config.respackopts_namespace()}.misc.redstoneTweaksTooltip.enabled": "§aEnabled§r",
        f"rpo.{config.respackopts_namespace()}.misc.redstoneTweaksTooltip.only_tooltip": "§eTooltip Only§r",
        # This line is disc-specific
        f"rpo.{config.respackopts_namespace()}.misc.echosOfLogging": "Echoes of Logging",
        f"rpo.{config.respackopts_namespace()}.misc.redstoneTweaksTooltip.tooltip":
            f"Adds comparator and length to the subtitle of a music disc\nE.g. " \
                # I owe code sanitizers an apology
                f"{(j := (i := list(disc_names_for_subtitle.values())[0]).find("${RTINFO"), i[:j] if j != -1 else i)[1]} "\
                    f'{COMPARATOR}{config.disc_index()[0].comparator_output} '
                    f"{CLOCK}{config.disc_index()[0].format_length()}\n" \
                    f"§c§lNOTE: This only works if you have the Redstone Tweaks resource pack enabled§r",
    } if with_rpo else {}
    
    return lambda: json.dumps({
        f"{config.our_namespace()}.version_check.{config.version()}": "Your version is up-to-date!",
        f"{config.our_namespace()}.respack_version": str(config.version()),
    } | previous_updates | disc_names_for_subtitle | disc_names_for_ui | variation_opts | rpo_specific)

FORMATTING_LIST = {
    "§0": "black",
    "§1": "dblue",
    "§2": "dgreen",
    "§3": "daqua",
    "§4": "dred",
    "§5": "dpurple",
    "§6": "gold",
    "§7": "gray",
    "§8": "dgray",
    "§9": "blue",
    "§a": "green",
    "§b": "aqua",
    "§c": "red",
    "§d": "lpurple",
    "§e": "yellow",
    "§f": "white",
    "§k": "obfus",
    "§l": "bold",
    "§m": "strike",
    "§n": "uline",
    "§o": "italic",
    "§r": "reset",
}

def efcisds(display: str, config_id: str) -> str:
    "Expandify formatting codes in subtitles display string"
    for i, j in FORMATTING_LIST.items():
        display.replace(i, "${SB%s}" % j)
    return display + "${RTINFOSB%s}" % config_id

def efciuids(display: str, config_id: str) -> str:
    "Expandify formatting codes in UI display string"
    for i, j in FORMATTING_LIST.items():
        display.replace(i, "${UI%s}" % j)
    return display + "${RTINFOUI%s}" % config_id

def lang_json_rpo() -> str:
    rTT = f"{config.respackopts_namespace()}.misc.redstoneTweaksTooltip"
    # Holy lord this is unreadable
    return json5.dumps({
        "expansions": {
            f"SB{j}": f"{config.respackopts_namespace()}.misc.formattingCodes == 'enabled' ? '{i}' : ''"
            for i, j in FORMATTING_LIST.items()
        } | {
            f"UI{j}": f"{config.respackopts_namespace()}.misc.formattingCodes != 'disabled' ? '{i}' : ''"
            for i, j in FORMATTING_LIST.items()
        } | {
            f"RTINFOSB{spec.config_id}": 
                f"{rTT} != 'disabled' ? ' §f{COMPARATOR}§7{spec.comparator_output} §f{CLOCK}§7{spec.format_length()}' : ''"
            for spec in config.disc_index()
        } | {
            f"RTINFOUI{spec.config_id}":
                f"{rTT} == 'enabled' ? ' §f{COMPARATOR}§7{spec.comparator_output} §f{CLOCK}§7{spec.format_length()}' : ''"
            for spec in config.disc_index()
        } | {
            # Disc-specific
            f"echoesOfLonging": f"{config.respackopts_namespace()}.misc.echoesOfLogging ? "\
                f"'{config.get_disc_spec("dazbee-echoes_of_longing").display.replace("Longing", "Logging")}':" \
                f"'{config.get_disc_spec("dazbee-echoes_of_longing").display}'"
        }
    })

def respackopts_json() -> str:
    variations = {
        spec.config_id: {
            "type": "enum",
            "default": "default",
            "values": ["default"] + [i.variation_id for i in spec.alts]
        }
        for spec in config.disc_index() if len(spec.alts) != 0
    }
    return json5.dumps({
        "id": config.respackopts_namespace(),
        "version": 14,
        "capabilities": ["FileFilter", "DirFilter"],
        "conf": {
            "misc": {
                "formattingCodes": {
                    "type": "enum",
                    "default": "enabled",
                    "values": ["disabled", "enabled", "only_ui"]
                },
                "redstoneTweaksTooltip": {
                    "type": "enum",
                    "default": "disabled",
                    "values": ["disabled", "enabled", "only_tooltip"]
                },
                # Disc-specific
                "echosOfLogging": False
            },
            "variations": variations
        }
    })