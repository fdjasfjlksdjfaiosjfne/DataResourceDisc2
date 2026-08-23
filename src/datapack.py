from pathlib import Path
import json
import typing
from src.config import Config, DiscSpec
import shutil
import re

CONFIG = Config()

def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding = "utf-8")

def init():
    root = CONFIG.debug_datapack_path()
    
    # Remove everything
    for path in root.iterdir():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    
    OUR_NAMESPACE = root / f"data/{CONFIG.our_namespace()}"
    MINECRAFT_NAMESPACE = root / f"data/minecraft"
    
    GENERATED_FILES: dict[Path, typing.Callable[[], str]] = {
        root / "pack.mcmeta": pack_mcmeta,
        OUR_NAMESPACE / "dialog/disc_selection.json": disc_selection_json,
        OUR_NAMESPACE / "function/load.mcfunction": load_function,
        OUR_NAMESPACE / "function/tick.mcfunction": tick_function,
        OUR_NAMESPACE / "function/apply_disc.mcfunction": apply_disc_function,
        OUR_NAMESPACE / "function/restore_disc.mcfunction": restore_disc_function,
        OUR_NAMESPACE / "function/info.mcfunction": info_function,
        OUR_NAMESPACE / f"predicate/{CONFIG.predicate("pack_info", False)}.json": lambda: json.dumps({
            "condition": "inverted",
            "term": {
                "condition": "entity_scores",
                "entity": "this",
                "scores": {
                    CONFIG.objective("pack_info"): 0
                }
            }
        }),
        OUR_NAMESPACE / f"predicate/{CONFIG.predicate("trigger_ui", False)}.json": lambda: json.dumps({
            "condition": "inverted",
            "term": {
                "condition": "entity_scores",
                "entity": "this",
                "scores": {
                    CONFIG.objective("trigger_ui"): 0
                }
            }
        }),
        MINECRAFT_NAMESPACE / "tags/dialog/quick_actions.json": lambda: json.dumps({"values": [f"{CONFIG.our_namespace()}:disc_selection"]}),
        MINECRAFT_NAMESPACE / "tags/function/load.json": lambda: json.dumps({"values": [f"{CONFIG.our_namespace()}:load"]}),
        MINECRAFT_NAMESPACE / "tags/function/tick.json": lambda: json.dumps({"values": [f"{CONFIG.our_namespace()}:tick"]}),
    } | {
        OUR_NAMESPACE / f"item_modifier/trans/{spec.id}.json": write_trans_item_modifer(spec.id)
        for spec in CONFIG.disc_index()
    } | {
        OUR_NAMESPACE / f"item_modifier/restore/{i}.json": write_restore_item_modifer(i)
        for i in CONFIG.vanilla_discs()
    } | {
        OUR_NAMESPACE / f"jukebox_song/{spec.id}.json": jukebox_song_definition(spec)
        for spec in CONFIG.disc_index()
    }
    for path, generator in GENERATED_FILES.items():
        print(f"Writing {path.relative_to(root)}...")
        write_file(path, generator())
    
    print(f"Copying pack.png for the data pack...")
    (Path(__file__).parent / f"textures/{CONFIG.datapack_pack_png_id()}.png").copy(root / "pack.png")

def pack_mcmeta() -> str:
    return json.dumps({
    "pack": {
        "min_format": CONFIG.datapack_pack_format(),
        "max_format": CONFIG.datapack_pack_format(),
        "description": f"[Ver {CONFIG.version()}] Provides technical details and dialogs to Configure select music discs"
    }
})

def disc_selection_json() -> str:
    actions = [{
        # Vanilla Disc
        "label": "Vanilla",
        "width": 325,
        "action": {
            "type": "run_command",
            "command": f"trigger {CONFIG.objective("select_disc")} set -1"
        }
    }]
    actions.extend(
        {
            "label": {"translate": f"{CONFIG.our_namespace()}:display.{disc_spec.id}.ui", "fallback": "§8Unavailable§r"},
            "width": 325,
            "action": {
                "type": "run_command",
                "command": f"trigger {CONFIG.objective("select_disc")} set {i}"
            }
        } for i, disc_spec in enumerate(CONFIG.disc_index(), start = 1)
    )
    return json.dumps({
        "type": "multi_action",
        "title": "Music Disc Texture Selection Screen",
        "columns": 1,
        "actions": actions,
    })

def load_function() -> str:
    return \
        f"scoreboard objectives add {CONFIG.objective("trigger_ui")} trigger\n" \
        f"scoreboard objectives add {CONFIG.objective("select_disc")} trigger\n" \
        f"scoreboard objectives add {CONFIG.objective("pack_info")} trigger\n" \
        f"scoreboard players set @a {CONFIG.objective("trigger_ui")} 0\n" \
        f"scoreboard players set @a {CONFIG.objective("select_disc")} 0\n" \
        f"scoreboard players set @a {CONFIG.objective("pack_info")} 0\n" \
        f"scoreboard players enable @a {CONFIG.objective("trigger_ui")}\n" \
        f"scoreboard players enable @a {CONFIG.objective("select_disc")}\n" \
        f"scoreboard players enable @a {CONFIG.objective("pack_info")}"

def tick_function() -> str:
    return \
        f"execute as @a[predicate={CONFIG.predicate("trigger_ui")}] run dialog show @s {CONFIG.our_namespace()}:disc_selection\n" \
        f"execute as @a[predicate={CONFIG.predicate("trigger_ui")}] run scoreboard players enable @a[predicate={CONFIG.our_namespace()}:{CONFIG.predicate("trigger_ui")}] {CONFIG.objective("trigger_ui")}\n" \
        f"execute as @a[predicate={CONFIG.predicate("trigger_ui")}] run scoreboard players set @a[predicate={CONFIG.our_namespace()}:{CONFIG.predicate("trigger_ui")}] {CONFIG.objective("trigger_ui")} 0\n" \
        f"execute as @a[scores={{{CONFIG.objective("select_disc")}=1..}}] run function {CONFIG.our_namespace()}:apply_disc\n" \
        f"execute as @a[scores={{{CONFIG.objective("select_disc")}=-1}}] run function {CONFIG.our_namespace()}:restore_disc\n" \
        f"execute as @a[predicate={CONFIG.our_namespace()}:{CONFIG.predicate("pack_info")}] run function {CONFIG.our_namespace()}:info"

def info_function() -> str:
    update_check = {
        "translate": f"{CONFIG.our_namespace()}.version_check.{CONFIG.version()}",
        "fallback": "§cYour resource pack is outdated!§r"
    }
    return "\n".join([
        f'tellraw @s {update_check}',
        f"tellraw @s ['Texture pack version: ', {{'translate': '{CONFIG.our_namespace()}.respack_version'}}]",
        f"tellraw @s '{f"Data pack version: {CONFIG.version()}"}'",
        f"scoreboard players set @s {CONFIG.objective("pack_info")} 0",
            f"scoreboard players enable @s {CONFIG.objective("pack_info")}"
    ])

def apply_disc_function() -> str:
    guard = "\n".join([
        "execute if items entity @s weapon.mainhand *[!jukebox_playable] run tellraw @s {text:'You must be holding an item capable of being played in a jukebox',color:'red'}",
        "execute if items entity @s weapon.mainhand air run tellraw @s {text:'You must be holding an item capable of being played in a jukebox',color:'red'}",
        "execute if items entity @s weapon.mainhand *[!jukebox_playable] run return fail",
        "execute if items entity @s weapon.mainhand air run return fail"
    ])
    trans = "\n".join(
        ("execute as @s[scores={%s=%d}] run item modify entity @s weapon.mainhand %s:trans/%s"
            % (CONFIG["names"]["scoreboard_objective"]["select_disc"], i, CONFIG.our_namespace(), disc_spec["id"])
        ) for i, disc_spec in enumerate(CONFIG["discs_index"], 1))
    
    epilouge = "\n".join([
        f"scoreboard players set @s {CONFIG.objective("select_disc")} 0",
        f"scoreboard players enable @s {CONFIG.objective("select_disc")}"
    ])
    return "\n".join([guard, trans, epilouge])

def restore_disc_function() -> str:
    guard = "\n".join([
        "execute if items entity @s weapon.mainhand *[!jukebox_playable] run tellraw @s {text:'You must be holding an item capable of being played in a jukebox',color:'red'}",
        "execute if items entity @s weapon.mainhand air run tellraw @s {text:'You must be holding an item capable of being played in a jukebox',color:'red'}",
        "execute if items entity @s weapon.mainhand *[!jukebox_playable] run return fail",
        "execute if items entity @s weapon.mainhand air run return fail"
    ])
    trans = "\n".join(
        ("execute if items entity @s weapon.mainhand music_disc_%s run item modify entity @s weapon.mainhand %s:restore/%s"
            % (disc, CONFIG.our_namespace(), disc)
        ) for disc in CONFIG["vanilla_discs"]
    )
    epilouge = "\n".join([
        f"scoreboard players set @s {CONFIG.objective("select_disc")} 0",
        f"scoreboard players enable @s {CONFIG.objective("select_disc")}"
    ])
    return "\n".join([guard, trans, epilouge])

def write_trans_item_modifer(id: str) -> typing.Callable[[], str]:
    return lambda: json.dumps({
        "function": "set_components",
        "components": {
            "jukebox_playable": f"{CONFIG.our_namespace()}:{id}"
        }
    })

def write_restore_item_modifer(id: str) -> typing.Callable[[], str]:
    return lambda: json.dumps({
        "function": "set_components",
        "components": {
            "jukebox_playable": f"minecraft:{id}"
        }
    })

def jukebox_song_definition(spec: DiscSpec):
    return lambda: json.dumps({
        "sound_event": {
            "sound_id": CONFIG.our_namespace() + ":music_disc." + spec.id,
            "range": spec.range
        },
        "description": {"translate": f"{CONFIG.our_namespace()}:display.{spec.id}.subtitle", "fallback": "§c???§r"},
        "length_in_seconds": spec.length,
        "comparator_output": spec.comparator_output
    })

if __name__ == "__main__":
    raise Exception("Run the wrong file dumbass")