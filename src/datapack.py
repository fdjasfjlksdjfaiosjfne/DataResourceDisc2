from pathlib import Path
import json
import typing
from logging import getLogger
from data import DATA, DiscSpec
import shutil
from itertools import product
from commands import *

logger = getLogger("disc_gen/datapack")

def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding = "utf-8")

def init():
    root = DATA.paths.datapack
    
    # Remove everything
    for path in root.iterdir():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    
    OUR_NAMESPACE = root / f"data/{DATA.our_namespace}"
    MINECRAFT_NAMESPACE = root / f"data/minecraft"
    
    GENERATED_FILES: dict[Path, typing.Callable[[], str]] = {
        root / "pack.mcmeta": pack_mcmeta,
        OUR_NAMESPACE / "dialog/disc_selection.json": disc_selection_json,
        OUR_NAMESPACE / "function/load.mcfunction": load_function,
        OUR_NAMESPACE / "function/tick.mcfunction": tick_function,
        OUR_NAMESPACE / "function/apply_disc.mcfunction": apply_disc_function,
        OUR_NAMESPACE / "function/restore_disc.mcfunction": restore_disc_function,
        OUR_NAMESPACE / "function/info.mcfunction": info_function,
        MINECRAFT_NAMESPACE / "tags/dialog/quick_actions.json": lambda: json.dumps({"values": [f"{DATA.our_namespace}:disc_selection"]}),
        MINECRAFT_NAMESPACE / "tags/function/load.json": lambda: json.dumps({"values": [f"{DATA.our_namespace}:load"]}),
        MINECRAFT_NAMESPACE / "tags/function/tick.json": lambda: json.dumps({"values": [f"{DATA.our_namespace}:tick"]}),
    } | {
        OUR_NAMESPACE / f"item_modifier/trans/{spec.id}.json": write_trans_item_modifer(spec.id)
        for spec in DATA.discs_index
    } | {
        OUR_NAMESPACE / f"item_modifier/cis/{i}.json": write_restore_item_modifer(i)
        for i in DATA.vanilla_discs
    } | {
        OUR_NAMESPACE / f"jukebox_song/{spec.id}.json": jukebox_song_definition(spec)
        for spec in DATA.discs_index
    } | {
        OUR_NAMESPACE / f"predicate/{predicate}.json": predicate_json(scores)
        for predicate, scores in zip(
            [DATA.predicates.trigger_ui, DATA.predicates.pack_info, DATA.predicates.select_disc, DATA.predicates.restore_disc],
            [DATA.scoreboard_objectives.trigger_ui, DATA.scoreboard_objectives.pack_info, DATA.scoreboard_objectives.select_disc, DATA.scoreboard_objectives.restore_disc]
        )
    }
    for path, generator in GENERATED_FILES.items():
        logger.debug(f"Writing {path.relative_to(root)}...")
        write_file(path, generator())
    
    logger.debug(f"Copying pack.png for the data pack...")
    (Path(__file__).parent.parent / f"assets/textures/{DATA.pack_cover.datapack}.png").copy(root / "pack.png")
    logger.info("Finish creating data pack!")

def pack_mcmeta() -> str:
    return json.dumps({
    "pack": {
        "min_format": DATA.pack_format.datapack,
        "max_format": DATA.pack_format.datapack,
        "description": f"[Ver {DATA.common_version}.{DATA.specific_version.datapack}] Provides technical details and dialogs to Configure select music discs"
    }
})

def predicate_json(score: str):
    return lambda: json.dumps({
        "condition": "inverted",
        "term": {
            "condition": "entity_scores",
            "entity": "this",
            "scores": {
                score: 0
            }
        }
    })

def disc_selection_json() -> str:
    actions = [{
        # Vanilla Disc
        "label": "Vanilla",
        "width": 325,
        "action": {
            "type": "run_command",
            "command": trigger_set(
                objective = DATA.scoreboard_objectives.restore_disc,
                value = 1
            )
        }
    }]
    actions.extend(
        {
            "label": {"translate": disc_spec.ui_key(), "fallback": "§8Unavailable§r"},
            "width": 325,
            "action": {
                "type": "run_command",
                "command": trigger_set(
                    objective = DATA.scoreboard_objectives.select_disc,
                    value = i
                )
            }
        } for i, disc_spec in enumerate(DATA.discs_index, start = 1)
    )
    return json.dumps({
        "type": "multi_action",
        "title": "Music Disc Texture Selection Screen",
        "columns": 1,
        "actions": actions,
    })

def load_function() -> str:
    return "\n".join(
        cmd(objective) for cmd, objective in product(
            [add_trigger_objective, lambda o: set_objective("@a", o, 0), lambda o: enable_objective("@a", o)],
            [DATA.scoreboard_objectives.select_disc, DATA.scoreboard_objectives.trigger_ui, DATA.scoreboard_objectives.pack_info, DATA.scoreboard_objectives.restore_disc]
        )
    )

def tick_function() -> str:
    return "\n".join([
        exe_as_all_with_pred(DATA.predicates.trigger_ui, f"dialog show @s {DATA.our_namespace}:disc_selection"),
        exe_as_all_with_pred(DATA.predicates.trigger_ui, enable_objective("@s", DATA.scoreboard_objectives.trigger_ui)),
        exe_as_all_with_pred(DATA.predicates.trigger_ui, set_objective("@s", DATA.scoreboard_objectives.trigger_ui, 0)),
        exe_as_all_with_pred(DATA.predicates.select_disc, run_function("apply_disc")),
        exe_as_all_with_pred(DATA.predicates.restore_disc, run_function("restore_disc")),
        exe_as_all_with_pred(DATA.predicates.pack_info, run_function("info"))
    ])

def info_function() -> str:
    return "\n".join([
        tellraw("@s", {
            "translate": f"{DATA.our_namespace}.version_check.{DATA.common_version}",
            "fallback": "§cYour resource pack is outdated!§r"
        }),
        tellraw("@s", f"Data pack version: {DATA.datapack_version()}"),
        tellraw("@s", [
            "Texture pack version: ",
            {"translate": DATA.respack_version_key(), "fallback": "§8Unavailable§r"}
        ]),
        set_objective("@s", DATA.scoreboard_objectives.pack_info, 0),
        enable_objective("@s", DATA.scoreboard_objectives.pack_info)
    ])

def apply_disc_function() -> str:
    return "\n".join([
        # Guard
        exe_if_item_mainhand("@s", "*[!jukebox_playable]", tellraw("@s", {
            "text": 'You must be holding an item capable of being played in a jukebox',
            "color": "red"
        })),
        exe_if_item_mainhand("@s", "air", tellraw("@s", {
            "text": 'You must be holding an item capable of being played in a jukebox',
            "color": "red"
        })),
        exe_if_item_mainhand("@s", "*[!jukebox_playable]", "return fail"),
        exe_if_item_mainhand("@s", "air", "return fail"),
        # Trans
        *[
            exe_as(
                "@s[scores={%s=%d}]" % (DATA.scoreboard_objectives.select_disc, i), 
                f"item modify entity @s weapon.mainhand {DATA.our_namespace}:trans/{spec.id}"
            ) for i, spec in enumerate(DATA.discs_index, 1)
        ],
        # Cleanup
        set_objective("@s", DATA.scoreboard_objectives.select_disc, 0),
        enable_objective("@s", DATA.scoreboard_objectives.select_disc)
    ])

def restore_disc_function() -> str:
    return "\n".join([
        # Guard
        exe_if_item_mainhand("@s", "*[!jukebox_playable]", tellraw("@s", {
            "text": 'You must be holding an item capable of being played in a jukebox',
            "color": "red"
        })),
        exe_if_item_mainhand("@s", "air", tellraw("@s", {
            "text": 'You must be holding an item capable of being played in a jukebox',
            "color": "red"
        })),
        exe_if_item_mainhand("@s", "*[!jukebox_playable]", "return fail"),
        exe_if_item_mainhand("@s", "air", "return fail"),
        # Restore
        *[
            exe_if_item_mainhand(
                "@s", f"minecraft:music_disc_{disc}",
                f"item modify entity @s weapon.mainhand {DATA.our_namespace}:cis/{disc}"
            ) for disc in DATA.vanilla_discs
        ],
        # Cleanup
        set_objective("@s", DATA.scoreboard_objectives.restore_disc, 0),
        enable_objective("@s", DATA.scoreboard_objectives.restore_disc)
    ])

def write_trans_item_modifer(id: str) -> typing.Callable[[], str]:
    return lambda: json.dumps({
        "function": "set_components",
        "components": {
            "jukebox_playable": f"{DATA.our_namespace}:{id}"
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
            "sound_id": spec.sound_id(),
            "range": spec.range
        },
        "description": {"translate": spec.subtitle_key()
                        #, "fallback": "§c???§r"
        },
        "length_in_seconds": spec.length,
        "comparator_output": spec.comparator_output
    })

if __name__ == "__main__":
    raise Exception("Run the wrong file dumbass")