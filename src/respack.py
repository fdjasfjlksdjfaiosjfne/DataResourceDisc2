from pathlib import Path
from typing import Callable
from data import DATA, OMNIDISC, DiscSpec, MISSING_DISC
from logging import getLogger
import json, json5
from respackopts import *
import shutil
import itertools
import string

CODEBASE_ROOT = Path(__file__).parent.parent
RPO_DATA = DATA.respackopts

logger = getLogger("disc_gen/respack")

def merge_all(*dicts: dict):
    omni = {}
    for d in dicts:
        omni |= d
    return omni

def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding = "utf-8")


def init():
    root = DATA.paths.respack
    
    
    for path in root.iterdir():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    
    init_sound_pack()
    
    ASSET_PATH = root / "assets"
    OUR_NAMESPACE = ASSET_PATH / DATA.our_namespace
    XP_TOME_NAMESPACE = ASSET_PATH / "xpbook"
    MINECRAFT_NAMESPACE = ASSET_PATH / "minecraft"
    ITEM_TEXTURES = OUR_NAMESPACE / "textures" / "item"
    ITEM_DEFS = MINECRAFT_NAMESPACE / "items"
    
    SOUNDS = root / f"assets/{DATA.our_namespace}/sounds"
    copy_sounds(SOUNDS)
    
    copy_disc_textures(ITEM_TEXTURES)
    copy_xp_tome_textures(XP_TOME_NAMESPACE / "textures/item")
    copy_vanilla_item_defs(ITEM_DEFS)

    GENERATED_TEXT_FILES = {
        # Item model supporting RPO
        OUR_NAMESPACE / f"models_rpo/item/{spec.id}.json": disc_item_model_json(spec, with_rpo = True)
        for spec in DATA.discs_index + [MISSING_DISC]
    } | {
        # Item model RPO
        OUR_NAMESPACE / f"models_rpo/item/{spec.id}.json.rpo": disc_item_model_json_rpo(spec)
        for spec in DATA.discs_index if spec.texture_alts
    } | {
        # Item model without RPO
        OUR_NAMESPACE / f"models/item/{spec.id}.json": disc_item_model_json(spec, with_rpo = False)
        for spec in DATA.discs_index + [MISSING_DISC]
    } | {
        # Item model definition
        OUR_NAMESPACE / f"items/{spec.id}.json": json.dumps({
            "model": {
                "type": "model",
                "model": f"{DATA.our_namespace}:{spec.id}"
            }
        }) for spec in DATA.discs_index + [MISSING_DISC]
    } | {
        XP_TOME_NAMESPACE / f"models_rpo/item/{tier.id}/charge_{charge}.json": json.dumps({
            "parent": "item/generated",
            "textures": {
                "layer0": f"xpbook:item/page",
                "layer1": f"xpbook:item/charges/${{color}}_{charge}",
                "layer2": f"xpbook:item/{tier.id}"
            }
        })
        for tier in DATA.tomes_index for charge in range(14)
    } | {
        XP_TOME_NAMESPACE / f"models/item/{tier.id}/charge_{charge}.json": json.dumps({
            "parent": "item/generated",
            "textures": {
                "layer0": f"xpbook:item/page",
                "layer1": f"xpbook:item/charges/{tier.default_xp_color}_{charge}",
                "layer2": f"xpbook:item/{tier.id}"
            }
        })
        for tier in DATA.tomes_index for charge in range(14) if DATA.add_tomes
    } | {
        XP_TOME_NAMESPACE / f"models_rpo/item/{tier.id}/charge_{charge}.json.rpo": json.dumps({
            "expansions": {
                "color": f"{DATA.respackopts.namespace}.{DATA.respackopts.config_namespace.xp_tomes}.{tier.id}"
            }
        })
        for tier in DATA.tomes_index for charge in range(14) if DATA.add_tomes
    } | {
        XP_TOME_NAMESPACE / f"items/xp_tome.json": xp_tome_item_def,
        OUR_NAMESPACE / f"models/.rpo": json.dumps({"condition": "false", "fallback": f"assets/{DATA.our_namespace}/models_rpo"}),
        MINECRAFT_NAMESPACE / "lang_rpo/en_us.json": us_english_json(with_rpo = True),
        MINECRAFT_NAMESPACE / "lang_rpo/en_us.json.rpo": lang_json_rpo,
        MINECRAFT_NAMESPACE / "lang/en_us.json": us_english_json(with_rpo = False),
        MINECRAFT_NAMESPACE / "lang/.rpo": json.dumps({"condition": "false", "fallback": f"assets/minecraft/lang_rpo/"}),
        XP_TOME_NAMESPACE / "models/.rpo": json.dumps({"condition": "false", "fallback": f"assets/xpbook/models_rpo"}),
        root / "respackopts.json5": respackopts_json,
        root / f"assets/{DATA.our_namespace}/sounds.json": sounds_json(),
        root / "pack.mcmeta": pack_mcmeta()
    }
    
    for path, generator_or_string in GENERATED_TEXT_FILES.items():
        logger.debug(f"Writing {path.relative_to(root)}...")
        write_file(path, generator_or_string if isinstance(generator_or_string, str) else generator_or_string())
    
    logger.debug(f"Copying pack.png for the resource pack...")
    (CODEBASE_ROOT / f"assets/textures/discs/{DATA.pack_cover.respack}.png").copy(root / "pack.png")
    logger.info(f"Resource pack generated!")

# This used to be its own resource pack
def init_sound_pack():
    root = DATA.paths.respack

def pack_mcmeta():
    return lambda: json.dumps({
        "pack": {
            "min_format": DATA.pack_format.respack,
            "max_format": DATA.pack_format.respack,
            "description": (
                f"[Ver {DATA.respack_version()}] Grants a new soul for custom discs"
            )
        }
    })

def disc_item_model_json_rpo(spec: DiscSpec) -> Callable[[], str]:
    key = f"{RPO_DATA.config_namespace.texture_variation}.{spec.rpo_id}"
    return lambda: json5.dumps({
        "expansions": {
            "variation": f"(('' || {key}) == 'default') ? '' : ('-' || {key})"
        }
    })

def disc_item_model_json(spec: DiscSpec, with_rpo: bool) -> Callable[[], str]:
    return lambda: json.dumps({
        "parent": "item/generated",
        "textures": {
            "layer0": f"{DATA.our_namespace}:item/{spec.id}" + ("${variation}" if with_rpo and spec.texture_alts else "")
        }
    })

def copy_disc_textures(path: Path):
    original_texture_dir = CODEBASE_ROOT / "assets/textures/discs"
    for spec in DATA.discs_index + [MISSING_DISC]:
        
        new_path = path / f"{spec.id}.png"
        logger.debug(f"Copying texture file to {new_path.relative_to(DATA.paths.respack)}...")
        
        png = original_texture_dir / f"{spec.id}.png"
        
        if (not png.exists()) or not png.is_file():
                logger.warning(f"{png.relative_to(CODEBASE_ROOT)} does not exist, using fallback")
                png = original_texture_dir / f"{MISSING_DISC.id}.png"
        
        new_path.parent.mkdir(parents=True, exist_ok=True)
        png.copy(new_path)
        
        if spec.mcmeta:
            write_file(path / f"{spec.id}.png.mcmeta", json.dumps(spec.mcmeta))
        
        for alt in spec.texture_alts:
            new_path = path / f"{spec.id}-{alt.variation_id}.png"
            logger.debug(f"Copying texture file to {new_path.relative_to(DATA.paths.respack)}...")
            png = original_texture_dir / f"{spec.id}-{alt.variation_id}.png"
            
            if (not png.exists()) or not png.is_file():
                logger.warning(f"{png.relative_to(CODEBASE_ROOT)} does not exist, using fallback")
                png = original_texture_dir / f"{MISSING_DISC.id}.png"
            
            new_path.parent.mkdir(parents=True, exist_ok=True)
            png.copy(new_path)
            
            if alt.mcmeta:
                write_file(path / f"{spec.id}-{alt.variation_id}.png.mcmeta", json.dumps(alt.mcmeta))

def xp_tome_item_def():
    return json.dumps({
        "model": {
            "type": "select",
            "property": "component",
            "component": "xpbook:max_xp",
            "cases": [
                {
                    "when": tome.max_xp,
                    "model": {
                        "type": "model",
                        "model": f"xpbook:item/{tome.id}/charge_13"
                    }
                } for tome in DATA.tomes_index
            ],
            "fallback": {
                "type": "model",
                "model": "xpbook:item/xp_tome"
            }
        }
    })

def copy_vanilla_item_defs(path: Path) -> None:
    for i in DATA.vanilla_discs:
        v = path / f"music_disc_{i}.json"
        v.parent.mkdir(parents = True, exist_ok = True)
        OMNIDISC.copy(v)

def copy_xp_tome_textures(path: Path) -> None:
    O = (Path(__file__).parent.parent / "assets/textures/xp_tomes")
    for p in O.rglob("*.png"):
        relative_path = str(p.relative_to(O))
        new_path = path / relative_path
        new_path.parent.mkdir(parents = True, exist_ok = True)
        p.copy(new_path)

def copy_sounds(path: Path):
    original_music_files = CODEBASE_ROOT / "assets/music/dist"
    for spec in DATA.discs_index:
        new_path = path / f"{spec.id}.ogg"
        logger.debug(f"Copying music file to {new_path.relative_to(DATA.paths.respack)}...")
        original_ogg = original_music_files / f"{spec.id}.ogg"
        if (not original_ogg.exists()) or not original_ogg.is_file():
            logger.warning(f"{original_ogg.relative_to(CODEBASE_ROOT)} does not exist, skipping")
            continue
        new_path.parent.mkdir(parents=True, exist_ok=True)
        new_path.touch()
        original_ogg.copy(new_path)

def sounds_json() -> str:
    return json.dumps({
        spec.sound_id().removeprefix(f"{DATA.our_namespace}:"): {
            "sounds": [{
                "name": f"{DATA.our_namespace}:{spec.id}",
                "stream": True
            }]
        } for spec in DATA.discs_index
    })

def us_english_json(with_rpo: bool) -> Callable[[], str]:
    previous_updates = {
        DATA.version_check_key(i): "Your resource pack should work fine!"
        for i in range(1, DATA.common_version)
    }
    
    disc_names_for_subtitle = {
        spec.subtitle_key(): spec.display_name if not with_rpo else "${SB%s}" % spec.rpo_id
        for spec in DATA.discs_index
    }
    
    disc_names_for_ui = {
        spec.ui_key(): spec.display_name if not with_rpo else "${UI%s}" % spec.rpo_id
        for spec in DATA.discs_index
    }

    
    texture_variation_opts = {}
    if with_rpo:
        for spec in DATA.discs_index:
            if spec.texture_alts:
                texture_variation_opts.update({
                    f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.texture_variation}.{spec.rpo_id}.default": spec.texture_variation_display_name,
                    f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.texture_variation}.{spec.rpo_id}": spec.display_name
                } | {
                    opt.rpo_option_key(): opt.variation_display_name
                    for opt in spec.texture_alts
                })
    
    display_name_variation_opts = {}
    if with_rpo:
        for spec in DATA.discs_index:
            if spec.texture_alts:
                texture_variation_opts.update({
                    f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.display_name_variation}.{spec.rpo_id}.default": spec.display_name_variation_display_name,
                    f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.display_name_variation}.{spec.rpo_id}": spec.display_name
                } | {
                    opt.rpo_option_key(): opt.variation_display_name
                    for opt in spec.display_name_alts
                })
    
    xp_tome_configs = {}
    if with_rpo:
        for tome in DATA.tomes_index:
            xp_tome_configs.update({
                f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.xp_tomes}.{tome.id}": tome.display_name
            } | {
                f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.xp_tomes}.{tome.id}.{color}": string.capwords(color.replace("_", " "))
                for color in DATA.tome_xp_color_index
            })
    
    rpo_specific = {
        f"rpo.{RPO_DATA.namespace}": "Custom Music Discs",
        f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.misc}": RPO_DATA.config_display_name.misc,
        f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.texture_variation}": RPO_DATA.config_display_name.texture_variation,
        f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.display_name_variation}": RPO_DATA.config_display_name.display_name_variation,
        f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.xp_tomes}": RPO_DATA.config_display_name.xp_tomes,
        f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.misc}.formattingCodes": "Enable formatting codes",
        f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.misc}.formattingCodes.enabled": "§aEnabled§r",
        f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.misc}.formattingCodes.disabled": "§cDisabled§r",
        f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.misc}.formattingCodes.only_ui": "§eUI Only§r",
        f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.misc}.redstoneTweaksTooltip": "Redstone Tweaks-styled Tooltip",
        f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.misc}.redstoneTweaksTooltip.disabled": "§cDisabled§r",
        f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.misc}.redstoneTweaksTooltip.enabled": "§aEnabled§r",
        f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.misc}.redstoneTweaksTooltip.only_tooltip": "§eTooltip Only§r",
        f"rpo.{RPO_DATA.namespace}.{RPO_DATA.config_namespace.misc}.redstoneTweaksTooltip.tooltip":
            f"Adds comparator and length to the subtitle of a music disc\nE.g. " \
                # I owe code sanitizers an apology
                f"{(j := (i := list(disc_names_for_subtitle.values())[0]).find("${RTINFO"), i[:j] if j != -1 else i)[1]} "\
                    f'{RT_COMPARATOR}{DATA.discs_index[0].comparator_output} '
                    f"{RT_CLOCK}{DATA.discs_index[0].format_length()}\n" \
                    f"§c§lNOTE: This only works if you have the Redstone Tweaks resource pack enabled§r",
    } if with_rpo else {}
    
    xp_tomes = {
        "item.xpbook.xp_tome.tier_1": "XP Tome",
        "item.xpbook.xp_tome.tier_2": "XP Tome+",
        "item.xpbook.xp_tome.tier_3": "XP Tome++",
    }
    
    other = {
        DATA.version_check_key(): "Your version is up-to-date!",
        f"{DATA.our_namespace}.respack_version": DATA.respack_version(),
    }
    
    return lambda: json.dumps(merge_all(
        previous_updates, disc_names_for_subtitle, disc_names_for_ui, 
        texture_variation_opts, rpo_specific, other, display_name_variation_opts, xp_tome_configs
    ))

def lang_json_rpo() -> str:
    redstone_tweaks_tooltip = f"{RPO_DATA.namespace}.{RPO_DATA.config_namespace.misc}.redstoneTweaksTooltip"
    display_name_vars = f"{RPO_DATA.namespace}.{RPO_DATA.config_namespace.display_name_variation}"
    
    subtitle_expansions, ui_expansions = {}, {}
    for spec in DATA.discs_index:
        sb_obj = mu_object(
            {"default": spec.display_name_in_mu_for_subtitles()} | {
                alt.variation_id: alt.display_name_in_mu_for_subtitles()
                for alt in spec.display_name_alts
            }
        )
        
        sb_argument = mu_ternary(
            mu_contains(display_name_vars, mu_string(spec.rpo_id)),
            true = f"{display_name_vars}.{spec.rpo_id}",
            false = mu_string("default")
        )
        
        sb_rt_ext = mu_ternary(
            mu_enum_nequals(redstone_tweaks_tooltip, "disabled"),
            mu_string(f' {RT_COMPARATOR}§7{spec.comparator_output} {RT_CLOCK}§7{spec.format_length()}§r'),
            mu_string("")
        )
        
        subtitle_expansions[f"SB{spec.rpo_id}"] = sb_obj + f"[{sb_argument}] || ({sb_rt_ext})"
        
        ui_obj = mu_object(
            {"default": spec.display_name_in_mu_for_ui()} | {
                alt.variation_id: alt.display_name_in_mu_for_ui()
                for alt in spec.display_name_alts
            }
        )
        
        ui_argument = mu_ternary(
            mu_contains(display_name_vars, mu_string(spec.rpo_id)),
            true = f"{display_name_vars}.{spec.rpo_id}",
            false = mu_string("default")
        )
        
        ui_rt_ext = mu_ternary(
            mu_enum_equals(redstone_tweaks_tooltip, "enabled"),
            mu_string(f' {RT_COMPARATOR}§7{spec.comparator_output} {RT_CLOCK}§7{spec.format_length()}§r'),
            mu_string("")
        )
        
        ui_expansions[f"UI{spec.rpo_id}"] = ui_obj + f"[{ui_argument}] || ({ui_rt_ext})"
    
    return json5.dumps({
        "expansions": subtitle_expansions | ui_expansions
    })

def respackopts_json() -> str:
    return json5.dumps({
        "id": RPO_DATA.namespace,
        "version": 14,
        "capabilities": ["FileFilter", "DirFilter"],
        "conf": {
            RPO_DATA.config_namespace.misc: {
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
            },
            RPO_DATA.config_namespace.texture_variation: {
                spec.rpo_id: {
                    "type": "enum",
                    "default": "default",
                    "values": ["default"] + [i.variation_id for i in spec.texture_alts]
                }
                for spec in DATA.discs_index if spec.texture_alts
            },
            RPO_DATA.config_namespace.display_name_variation: {
                spec.rpo_id: {
                    "type": "enum",
                    "default": "default",
                    "values": ["default"] + [i.variation_id for i in spec.display_name_alts]
                } for spec in DATA.discs_index if spec.display_name_alts
            },
            RPO_DATA.config_namespace.xp_tomes: {
                tome.id: {
                    "type": "enum",
                    "default": tome.default_xp_color,
                    "values": DATA.tome_xp_color_index,
                } for tome in DATA.tomes_index
            }
        }
    })