from pathlib import Path
import json
import typing
from logging import getLogger
from data import DATA, Constants, DiscSpec, MISSING_DISC
import shutil
from itertools import chain, product
from commands import *

logger = getLogger("disc_gen/datapack")

def join(*l):
    return "\n".join(str(i) for i in l)

NS = DATA.our_namespace
SCORE_OBJS = DATA.scoreboard_objectives
PRED = DATA.predicates

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
    
    if DATA.add_tomes: add_tomes()
    
    OUR_NAMESPACE = root / f"data/{DATA.our_namespace}"
    
    GENERATED_FILES: dict[Path, str | typing.Callable[[], str]] = {
        root / "pack.mcmeta": pack_mcmeta,
        Constants.disc_selection_dialog_path: disc_selection_json,
        Constants.load_fn_path: load_function,
        Constants.tick_fn_path: tick_function,
        Constants.apply_disc_fn_path: apply_disc_function,
        Constants.restore_disc_fn_path: restore_disc_function,
        Constants.info_fn_path: info_function,
        Constants.is_holding_disc_fn_path: is_holding_disc_function,
        Constants.quick_actions_dialog_tag_path: json.dumps({"values": [Constants.disc_selection_dialog, Constants.configure_xp_tome_dialog]}),
        Constants.pause_screen_additions_dialog_tag_path: json.dumps({"values": [Constants.disc_selection_dialog, Constants.configure_xp_tome_dialog]}),
        Constants.load_fn_tag_path: json.dumps({"values": [Constants.load_fn]}),
        Constants.tick_fn_tag_path: json.dumps({"values": [Constants.tick_fn]}),
        
    } | {
        OUR_NAMESPACE / f"item_modifier/trans/{spec.id}.json": write_trans_item_modifer(spec)
        for spec in DATA.discs_index
    } | {
        OUR_NAMESPACE / f"item_modifier/cis/{i}.json": write_restore_item_modifer(i)
        for i in DATA.vanilla_discs
    } | {
        OUR_NAMESPACE / f"jukebox_song/{spec.id}.json": jukebox_song_definition(spec)
        for spec in DATA.discs_index
    } | {
        OUR_NAMESPACE / f"predicate/{predicate}.json": predicate_json(scores)
        for predicate, scores in zip(PRED, SCORE_OBJS)
    } | {
        OUR_NAMESPACE / f"recipe/{name}.json": json.dumps(d)
        for name, d in DATA.recipes.items()

    } | ({} if not DATA.add_tomes else {
        Constants.configure_xp_tome_fn_path: configure_xp_tome_fn,
        Constants.configure_xp_tome_dialog_path: configure_xp_tome_dialog,
    })
    
    for path, generator_or_string in GENERATED_FILES.items():
        logger.debug(f"Writing {path.relative_to(root)}...")
        write_file(path, generator_or_string if isinstance(generator_or_string, str) else generator_or_string())
    
    logger.debug(f"Copying pack.png for the data pack...")
    (Path(__file__).parent.parent / f"assets/textures/discs/{DATA.pack_cover.datapack}.png").copy(root / "pack.png")
    logger.info("Finish creating data pack!")

def pack_mcmeta() -> str:
    return json.dumps({
    "pack": {
        "min_format": DATA.pack_format.datapack,
        "max_format": DATA.pack_format.datapack,
        "description": f"[Ver {DATA.common_version}.{DATA.specific_version.datapack}] Declares custom discs"
    }
})

def configure_xp_tome_dialog():
    return json.dumps({
        "type": "confirmation",
        "title": "Configure XP Tome",
        "body": [
            {
                "type": "plain_message",
                "contents": "Modify your XP tome behavior here.."
            },
            {
                "type": "plain_message",
                "contents": {"text": "Note: You must hold an XP tome on your hand!", "color": "red"}
            }
        ],
        "inputs": [
            {
                "type": "boolean",
                "key": "retrieve_orbs",
                "label": "Retreives XP as XP orbs",
                "initial": False,
                "on_true": "1",
                "on_false": "0"
            },
            {
                "type": "boolean",
                "key": "get_until_next",
                "label": "Recieve XP until you reach the next level",
                "initial": True,
                "on_true": "1",
                "on_false": "0"
            },
            {
                "type": "boolean",
                "key": "store_until_previous",
                "label": "Store XP until you reach the previous level",
                "initial": False,
                "on_true": "1",
                "on_false": "0"
            }
        ],
        "yes": {
            "label": "Confirm Options",
            "action": {
                "type": "dynamic/run_command",
                "template": f"trigger {SCORE_OBJS.configure_xp_tomes} set 1$(retrieve_orbs)$(get_until_next)$(store_until_previous)"
            }
        },
        "no": {
            "label": "Discard"
        }
    })

def add_tomes():
    for tome in DATA.tomes_index:
        # Recipe JSON
        write_file(tome.recipe_json_path(), json.dumps({
            "type": "minecraft:crafting_shaped",
            "key": tome.recipe_key,
            "pattern": tome.recipe_pattern,
            "result": {
                "id": f"xpbook:xp_tome",
                "components": {
                    "minecraft:item_name": tome.display_name,
                    "xpbook:max_xp": tome.max_xp
                } | ({"xpbook:retrieve_xp_orbs": {}} if tome.retrieve_xp_orbs else {})
                  | ({"xpbook:retrieve_until_next_level": {} if tome.retrieve_until_next_level else {}})
                  | ({"xpbook:store_until_previous_level": {} if tome.store_until_previous_level else {}})
            }
        }))
    # Item modifiers
    imp = DATA.paths.datapack / "data/xpbook/item_modifier"
    for opt in ["retrieve_xp_orbs", "retrieve_until_next_level", "store_until_previous_level"]:
        write_file(imp / f"{opt}_off.json", json.dumps({
            "function": "set_components",
            "components": {
                f"!xpbook:{opt}": {}
            }
        }))
        write_file(imp / f"{opt}_on.json", json.dumps({
            "function": "set_components",
            "components": {
                f"xpbook:{opt}": {}
            }
        }))

def predicate_json(score: str):
    return json.dumps({
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
            "command": TriggerCmd.add(SCORE_OBJS.restore_disc).build()
        }
    }]
    actions.extend(
        {
            "label": {"translate": disc_spec.ui_key(), "fallback": "§8Unavailable§r"},
            "width": 325,
            "action": {
                "type": "run_command",
                "command": TriggerCmd.set(SCORE_OBJS.select_disc, i).build()
            }
        } for i, disc_spec in enumerate(DATA.discs_index, start = 1)
    )
    return json.dumps({
        "type": "multi_action",
        "title": "Music Disc Texture Selection Screen",
        "external_title": "Select disc...",
        "columns": 1,
        "actions": actions,
    })

def load_function() -> str:
    i = []
    for objct in SCORE_OBJS:
        i.append(ScoreboardCmd.Objectives.add(objct, ScoreboardSingleCriteria.TRIGGER))
        i.append(ScoreboardCmd.Players.set(AllPlayers(), objct, 0))
        i.append(ScoreboardCmd.Players.enable(AllPlayers(), objct))
    return join(*i)

def tick_function() -> str:
    return join(
        ExecuteCmd().as_(AllPlayers().predicate(f"{NS}:{PRED.trigger_disc_ui}")).run(DialogCmd.show(Executor(), Constants.disc_selection_dialog)),
        ExecuteCmd().as_(AllPlayers().predicate(f"{NS}:{PRED.trigger_disc_ui}")).run(ScoreboardCmd.Players.enable(Executor(), SCORE_OBJS.trigger_disc_ui)),
        ExecuteCmd().as_(AllPlayers().predicate(f"{NS}:{PRED.trigger_disc_ui}")).run(ScoreboardCmd.Players.set(Executor(), SCORE_OBJS.trigger_disc_ui, 0)),
        ExecuteCmd().as_(AllPlayers().predicate(f"{NS}:{PRED.trigger_tome_config_ui}")).run(DialogCmd.show(Executor(), Constants.configure_xp_tome_dialog)),
        ExecuteCmd().as_(AllPlayers().predicate(f"{NS}:{PRED.trigger_tome_config_ui}")).run(ScoreboardCmd.Players.enable(Executor(), SCORE_OBJS.trigger_tome_config_ui)),
        ExecuteCmd().as_(AllPlayers().predicate(f"{NS}:{PRED.trigger_tome_config_ui}")).run(ScoreboardCmd.Players.set(Executor(), SCORE_OBJS.trigger_tome_config_ui, 0)),
        ExecuteCmd().as_(AllPlayers().predicate(f"{NS}:{PRED.select_disc}")).unless_function(Constants.apply_disc_fn).run(
            TellrawCmd(Executor(), TextComponent().text('You must be holding an item capable of being played in a jukebox').color(Color.RED))
        ),
        ExecuteCmd().as_(AllPlayers().predicate(f"{NS}:{PRED.restore_disc}")).unless_function(Constants.restore_disc_fn).run(
            TellrawCmd(Executor(), TextComponent().text('You must be holding an item capable of being played in a jukebox').color(Color.RED))
        ),
        ExecuteCmd().as_(AllPlayers().predicate(f"{NS}:{PRED.configure_xp_tomes}")).run(FunctionCmd.run(Constants.configure_xp_tome_fn)),
        ExecuteCmd().as_(AllPlayers().predicate(f"{NS}:{PRED.select_disc}")).run(ScoreboardCmd.Players.set(Executor(), SCORE_OBJS.select_disc, 0)),
        ExecuteCmd().as_(AllPlayers().predicate(f"{NS}:{PRED.restore_disc}")).run(ScoreboardCmd.Players.set(Executor(), SCORE_OBJS.restore_disc, 0)),
        ExecuteCmd().as_(AllPlayers().predicate(f"{NS}:{PRED.configure_xp_tomes}")).run(ScoreboardCmd.Players.set(Executor(), SCORE_OBJS.configure_xp_tomes, 0)),
        ExecuteCmd().as_(AllPlayers().predicate(f"{NS}:{PRED.pack_info}")).run(FunctionCmd.run(f"{NS}:info"))
    )

def info_function() -> str:
    return join(
        TellrawCmd(Executor(), TextComponent().translatable(f"{NS}.version_check.{DATA.common_version}", "§cYour resource pack is outdated!§r")),
        TellrawCmd(Executor(), TextComponent().text(f"Data pack version: {DATA.datapack_version()}")),
        TellrawCmd(Executor(), NBTList([
            TextComponent().text("Texture pack version: "),
            TextComponent().translatable(DATA.respack_version_key(), "§8Unavailable§r")
        ])),
        ScoreboardCmd.Players.set(Executor(), SCORE_OBJS.pack_info, 0),
        ScoreboardCmd.Players.enable(Executor(), SCORE_OBJS.pack_info)
    )

def is_holding_disc_function():
    return join(
        *[ExecuteCmd().if_items_entity(Executor(), "weapon.mainhand", f"music_disc_{d}").run(ReturnCmd.return_(1)) for d in DATA.vanilla_discs],
        ExecuteCmd().if_items_entity(Executor(), "weapon.mainhand", "*[jukebox_playable]").run(ReturnCmd.return_(1)),
        ReturnCmd.return_(0)
    )

def apply_disc_function() -> str:
    return join(
        ScoreboardCmd.Players.enable(Executor(), SCORE_OBJS.select_disc),
        ExecuteCmd().unless_function(Constants.is_holding_disc_fn).run(ReturnCmd.fail()),
        *[ExecuteCmd().as_(Executor().scores({SCORE_OBJS.select_disc: i})).run(
            ItemCmd.modify_entity(Executor(), "weapon.mainhand", f"{NS}:trans/{spec.id}")
        ) for i, spec in enumerate(DATA.discs_index, 1)],
        ReturnCmd.return_(1)
    )

def restore_disc_function() -> str:
    return join(
        ScoreboardCmd.Players.enable(Executor(), SCORE_OBJS.select_disc),
        ExecuteCmd().unless_function(Constants.is_holding_disc_fn).run(ReturnCmd.fail()),
        ScoreboardCmd.Players.set(Executor(), SCORE_OBJS.restore_disc, 0),
        ScoreboardCmd.Players.enable(Executor(), SCORE_OBJS.restore_disc),
        *[ExecuteCmd().if_items_entity(Executor(), "weapon.mainhand", f"minecraft:music_disc_{disc}")
            .run(ItemCmd.modify_entity(Executor(), "weapon.mainhand", f"{NS}:cis/{disc}"))
        for disc in DATA.vanilla_discs], 
        ReturnCmd.return_(1)
    )

def configure_xp_tome_fn():
    return join(
        ScoreboardCmd.Players.enable(Executor(), SCORE_OBJS.configure_xp_tomes),
        # * VALIDATION
        ExecuteCmd().unless_items_entity(Executor(), "weapon.mainhand", "xpbook:xp_tome").run(
            TellrawCmd(Executor(), TextComponent().text("You must hold a tome!").color("red"))
        ),
        ExecuteCmd().unless_items_entity(Executor(), "weapon.mainhand", "xpbook:xp_tome").run(ReturnCmd.fail()),
        ExecuteCmd().unless_score_matches(Executor(), SCORE_OBJS.configure_xp_tomes, IntRange(1000, 1111)).run(
            TellrawCmd(Executor(), TextComponent.expand([
                TextComponent().text("This `/trigger` command is not meant to be used manually!\\n"),
                TextComponent().text("I do not gurantee whether the command works properly or not with an arbitrary number.\\n"),
                TextComponent().text("How about booting up its dedicated UI?").click_event(ClickEvent.SHOW_DIALOG, Constants.configure_xp_tome_dialog)
            ]))
        ),
        ExecuteCmd().unless_score_matches(Executor(), SCORE_OBJS.configure_xp_tomes, IntRange(1000, 1111)).run(ReturnCmd.fail()),
        # * ACTUALLY TRYING TO CONFIGURE
        ScoreboardCmd.Players.remove(Executor(), SCORE_OBJS.configure_xp_tomes, 1000),
        ExecuteCmd().if_score_matches(Executor(), SCORE_OBJS.configure_xp_tomes, IntRange.min(100)).run(
            ItemCmd.modify_entity(Executor(), "weapon.mainhand", f"xpbook:retrieve_xp_orbs_on")
        ),
        ExecuteCmd().unless_score_matches(Executor(), SCORE_OBJS.configure_xp_tomes, IntRange.min(100)).run(
            ItemCmd.modify_entity(Executor(), "weapon.mainhand", f"xpbook:retrieve_xp_orbs_off")
        ),
        ExecuteCmd().if_score_matches(Executor(), SCORE_OBJS.configure_xp_tomes, IntRange.min(100)).run(
            ScoreboardCmd.Players.remove(Executor(), SCORE_OBJS.configure_xp_tomes, 100)
        ),
        ExecuteCmd().if_score_matches(Executor(), SCORE_OBJS.configure_xp_tomes, IntRange.min(10)).run(
            ItemCmd.modify_entity(Executor(), "weapon.mainhand", f"xpbook:retrieve_until_next_level_on")
        ),
        ExecuteCmd().unless_score_matches(Executor(), SCORE_OBJS.configure_xp_tomes, IntRange.min(10)).run(
            ItemCmd.modify_entity(Executor(), "weapon.mainhand", f"xpbook:retrieve_until_next_level_off")
        ),
        ExecuteCmd().if_score_matches(Executor(), SCORE_OBJS.configure_xp_tomes, IntRange.min(10)).run(
            ScoreboardCmd.Players.remove(Executor(), SCORE_OBJS.configure_xp_tomes, 10)
        ),
        ExecuteCmd().if_score_matches(Executor(), SCORE_OBJS.configure_xp_tomes, IntRange.min(1)).run(
            ItemCmd.modify_entity(Executor(), "weapon.mainhand", f"xpbook:store_until_previous_level_on")
        ),
        ExecuteCmd().unless_score_matches(Executor(), SCORE_OBJS.configure_xp_tomes, IntRange.min(1)).run(
            ItemCmd.modify_entity(Executor(), "weapon.mainhand", f"xpbook:store_until_previous_level_off")
        ),
        ScoreboardCmd.Players.set(Executor(), SCORE_OBJS.configure_xp_tomes, 0)
    )

def write_trans_item_modifer(spec: DiscSpec) -> typing.Callable[[], str]:
    return json.dumps({
        "function": "set_components",
        "components": {
            "minecraft:jukebox_playable": f"{DATA.our_namespace}:{spec.id}",
            "minecraft:lore": spec.lore
        }
    })

def write_restore_item_modifer(id: str) -> typing.Callable[[], str]:
    return json.dumps({
        "function": "set_components",
        "components": {
            "minecraft:jukebox_playable": f"minecraft:{id}",
            "minecraft:lore": []
        }
    })

def jukebox_song_definition(spec: DiscSpec):
    return json.dumps({
        "sound_event": {
            "sound_id": spec.sound_id(),
            "range": spec.range
        },
        "description": [
            {"translate": spec.subtitle_key(), "fallback": "§c???§r"}
        ],
        "length_in_seconds": spec.length,
        "comparator_output": spec.comparator_output
    })

if __name__ == "__main__":
    raise Exception("Run the wrong file dumbass")