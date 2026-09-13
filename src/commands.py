"""A module contains OOP warppers of various Minecraft commands and data formats.
"""

import re
from typing import Any, Literal, Self
import traceback, sys
from logging import getLogger
from mc_objects import *

logger = getLogger("disc_gen/commands")

def excepthook(exc_type, exc, tb):
    if isinstance(exc, CommandSyntaxException):
        print(exc.source, file = sys.stderr)
        print(" " * (exc.position[0] + 1) + "^" * (exc.position[1] - exc.position[0]), file = sys.stderr)
        print(f"{exc_type.__name__}: {exc}", file = sys.stderr)
        print()
        traceback.print_tb(tb, file = sys.stderr)
    else:
        sys.__excepthook__(exc_type, exc, tb)

sys.excepthook = excepthook

class CommandSyntaxException(Exception):
    def __init__(self, message, source=None, position=None):
        super().__init__(message)
        self.source = source
        self.position = position

class Command:
    """The base class for command classes.
    
    This class in particular simply store a string 
    and return it when building the string.
    """
    
    def __init__(self, command: str):
        self._command = command
    def __str__(self): return self.build()
    def build(self):
        """Returns a usable version of the command (without the `/`).
        
        Does the same thing as `str(self)`.
        
        Override this method if you wish to modify the parsing behavior.
        """
        return self._command.strip()

class ExecuteCmd(Command):
    """An OOP/builder representation of the /execute command.
    
    Using `str()` returns the command (without the preceding `/`).
    
    Usage:
    
    ```
    >>> ExecuteCmd().as_(NearestPlayer()).run(ScoreboardCmd.Players.set(Self(), "ns:objective", 42))
    "execute as @p run scoreboard players set @s ns:objective 42"
    ```
    """
    
    def __init__(self):
        self._command = "execute"
        self._clauses = []
        self._last_clause_position = None

    def _append_clause(self, clause: str, command: str) -> Self:
        self._last_clause_position = len(self._command) - 1
        if self._clauses and self._clauses[-1] == "run":
            raise CommandSyntaxException(
                "No subcommands can be added after the 'run' subcommand",
                self._command + f" {command}" + "...",
                (len(self._command), len(self._command + str(command)))
            )
        self._command += f" {command}"
        self._clauses.append(clause)
        return self

    def _validate_clauses(self):
        if not self._clauses:
            raise CommandSyntaxException(
                "There are no subcommands!",
                self._command,
                (0, len(self._command) - 1)
            )
        valid_tail = (
            # A condition subcommand that is *not* `(if|unless) function`
            (("if" in self._clauses[-1] or "unless" in self._clauses[-1]) and "function" not in self._clauses[-1])
            # Or `run`
            or self._clauses[-1] == "run"
        )
        if not valid_tail:
            raise CommandSyntaxException(
                f"{self._clauses[-1]} cannot be the last subcommand.",
                self._command,
                (self._last_clause_position + 1, len(self._command) - 1)
            )
        return self
    
    def build(self):
        self._validate_clauses()
        return self._command
    
    def align(self, swizzle: str):
        """Updates the execution position, aligning to its current block position (integer 
        coordinates). Applies only along specified axes.
        
        Effectively floors the coordinates (i.e., rounds the coordinates down).
        
        The `swizzle` argument accepts any non-repeating combination of the characters 
        'x', 'y', and 'z'. Axes can be declared in any order, but they cannot duplicate.
        """
        if set(swizzle) - {"x", "y", "z"}:
            raise ValueError("'swizzle' must only contain 'x', 'y' or 'z'")
        if len(swizzle) > 3:
            raise ValueError("'swizzle' must not repeat any characters")
        return self._append_clause("align", f"align {swizzle}")

    def anchored(self, anchor: Literal["eyes", "feet"]) -> Self:
        """Sets the execution anchor to the eyes or feet. Defaults to feet.
        
        Effectively recenters local coordinates on either the eyes or feet, also changing 
        the angle of the facing subcommand (of `/execute` and `/teleport`) works off of.
        """
        
        return self._append_clause("anchored", f"anchored {anchor}")
    
    def as_(self, target_selector: TargetSelector) -> Self:
        """Sets the executor to target entity, without changing execution position, 
        rotation, dimension, and anchor.
        """
        
        return self._append_clause("as", f"as {target_selector!s}")
    
    def at(self, entity_name: Entity):
        """Sets the execution position, rotation, and dimension to match those of 
        an entity; does not change executor.
        """
        
        return self._append_clause("at", f"at {entity_name!s}")
    
    def facing(self, pos: Position) -> Self:
        """Sets the execution rotation to face a given point, as viewed from its 
        anchor (either the eyes or the feet).
        """
        return self._append_clause("facing", f"facing {pos}")
    
    def in_(self, dimension: str) -> Self:
        """Sets the execution dimension and execution position.
        
        It respects dimension scaling for relative and local coordinates; the 
        execution position (only the X/Z part) is divided by 8 when changing 
        from the Overworld to the Nether, and is multiplied by 8 when vice versa. 
        Applies to custom dimensions as well.
        """
        
        return self._append_clause("in", f"in {dimension}")
    
    def on(self, relation: Relation) -> Self:
        """Updates the executor to entities selected based on relation to the 
        current executor entity. without changing execution position, rotation, 
        dimension, and anchor.
        """
        
        return self._append_clause("on", f"on {relation}")
    
    def positioned(self, position: Position) -> Self:
        """Sets the execution position, without changing execution rotation or dimension.
        """
        return self._append_clause("positioned", f"positioned {position}")
    
    def positioned_as(self, entity: Entity):
        """Sets the execution position to match an entity's position, without changing execution rotation or dimension.
        """
        return self._append_clause("positioned", f"positioned as {entity!s}")
    
    def positioned_over(self, heightmap: Heightmap):
        """Sets the execution position at one block above the Y-level stored in the specified heightmap, without changing execution rotation or dimension.
        """
        return self._append_clause("positioned", f"positioned over {heightmap}")
    
    def rotated(self, rotation: str) -> Self:
        """Sets the execution rotation.
        """
        return self._append_clause("rotated", f"rotated {rotation}")
    
    def rotated_as(self, entity: Entity) -> Self:
        """Sets the execution rotation to match an entity's rotatiion.
        """
        return self._append_clause("rotated", f"rotated as {entity!s}")
    
    def summon(self, entity: str) -> Self:
        """Summons a new entity at execution position and changes the executor to this summoned entity. 
        """
        return self._append_clause("summon", f"summon {entity}")
    
    def if_data_entity(self, entity: Entity, path) -> Self:
        """Checks whether the targeted entity has any data tag for a given path.
        """
        return self._append_clause("if", f"if data entity {entity} {path}")
    
    def unless_data_entity(self, entity: Entity, path) -> Self:
        """Checks whether the targeted entity has no data tag for a given path.
        """
        return self._append_clause("unless", f"unless data entity {entity} {path}")

    def if_block(self, position: BlockPos, block: str) -> Self:
        return self._append_clause("if", f"if block {position} {block}")

    def unless_block(self, position: BlockPos, block: str) -> Self:
        return self._append_clause("unless", f"unless block {position} {block}")

    def if_blocks(self, start: str, end: str, destination: str, scan: Literal["all", "masked"]) -> Self:
        return self._append_clause("if", f"if blocks {start} {end} {destination} {scan}")

    def unless_blocks(self, start: str, end: str, destination: str, scan: Literal["all", "masked"]) -> Self:
        return self._append_clause("unless", f"unless blocks {start} {end} {destination} {scan}")

    def if_data_block(self, position: BlockPos, path: str) -> Self:
        return self._append_clause("if", f"if data block {position} {path}")

    def unless_data_block(self, position: BlockPos, path: str) -> Self:
        return self._append_clause("unless", f"unless data block {position} {path}")

    def if_data_storage(self, storage: str, path: str) -> Self:
        return self._append_clause("if", f"if data storage {storage} {path}")

    def unless_data_storage(self, storage: str, path: str) -> Self:
        return self._append_clause("unless", f"unless data storage {storage} {path}")

    def if_dimension(self, dimension: str) -> Self:
        return self._append_clause("if", f"if dimension {dimension}")

    def unless_dimension(self, dimension: str) -> Self:
        return self._append_clause("unless", f"unless dimension {dimension}")

    def if_entity(self, entity: Entity) -> Self:
        return self._append_clause("if", f"if entity {entity}")

    def unless_entity(self, entity: Entity) -> Self:
        return self._append_clause("unless", f"unless entity {entity}")

    def if_loaded(self, position: Position) -> Self:
        return self._append_clause("if", f"if loaded {position}")

    def unless_loaded(self, position: Position) -> Self:
        return self._append_clause("unless", f"unless loaded {position}")
    
    def if_function(self, function) -> Self:
        """Checks if function(s) are non-void and the return value is non-zero. 
        
        Terminates current branch unless the function's return value is non-zero. 
        Doesn't change any execution context.
        Unlike other conditional subcommands, this subcommand can modify the world 
        depending on the function(s) that are tested. It also cannot be placed at 
        the end of the subcommand chain.
        """
        return self._append_clause("if function", f"if function {function}")
        
    def unless_function(self, function) -> Self:
        """Checks if function(s) are void or the return value is zero.
        
        Terminates current branch if the function's return value is non-zero.
        Doesn't change any execution context.
        Unlike other conditional subcommands, this subcommand can modify the world 
        depending on the function(s) that are tested. It also cannot be placed at 
        the end of the subcommand chain.
        """
        return self._append_clause("unless function", f"unless function {function}")
    
    def if_items_entity(self, entity: Entity, slot: str, path) -> Self:
        """Checks for a matching item in the provided inventory slots.
        """
        return self._append_clause("if", f"if items entity {entity} {slot} {path}")

    def if_items_block(self, position: BlockPos, slot: str, item: str) -> Self:
        return self._append_clause("if", f"if items block {position} {slot} {item}")
        
    def unless_items_entity(self, entity: Entity, slot: str, path) -> Self:
        """Checks for a matching item in the provided inventory slots.
        """
        return self._append_clause("unless", f"unless items entity {entity} {slot} {path}")

    def unless_items_block(self, position: BlockPos, slot: str, item: str) -> Self:
        return self._append_clause("unless", f"unless items block {position} {slot} {item}")
    
    def if_predicate(self, predicate: str) -> Self:
        """Checks whether the predicate successes.
        """
        return self._append_clause("if", f"if predicate {predicate}")
    
    def unless_predicate(self, predicate: str) -> Self:
        """Checks whether the predicate fails.
        """
        return self._append_clause("unless", f"unless predicate {predicate}")
    
    def if_score_compares(
            self, target: ScoreHolder, target_objective: str, 
            compare: Compare, source: ScoreHolder, source_objective: str) -> Self:
        """Check whether a score has the specific relation to another score.
        """
        return self._append_clause("if", f"if score {target} {target_objective} {compare} {source} {source_objective}")
    
    def unless_score_compares(
            self, target: ScoreHolder, target_objective: str, 
            compare: Compare, source: ScoreHolder, source_objective: str) -> Self:
        """Check whether a score has the opposite relation to another score.
        """
        return self._append_clause("unless", f"unless score {target} {target_objective} {compare} {source} {source_objective}")
    
    def if_score_matches(self, target: ScoreHolder, target_objective: str, range: IntOrIntRange):
        """Check whether a score is in a given range.
        """
        return self._append_clause("if", f"if score {target} {target_objective} matches {range}")
    
    def unless_score_matches(self, target: ScoreHolder, target_objective: str, range: IntOrIntRange):
        """Check whether a score is not in a given range.
        """
        return self._append_clause("unless", f"unless score {target} {target_objective} matches {range}")

    def store_result_score(self, target: ScoreHolder, objective: str) -> Self:
        return self._append_clause("store", f"store result score {target} {objective}")

    def store_success_score(self, target: ScoreHolder, objective: str) -> Self:
        return self._append_clause("store", f"store success score {target} {objective}")

    def store_result_bossbar(self, bossbar: str, value: Literal["value", "max"]) -> Self:
        return self._append_clause("store", f"store result bossbar {bossbar} {value}")

    def store_success_bossbar(self, bossbar: str, value: Literal["value", "max"]) -> Self:
        return self._append_clause("store", f"store success bossbar {bossbar} {value}")

    def store_result_entity(self, entity: Entity, path: str, data_type: str, scale: float | int) -> Self:
        return self._append_clause("store", f"store result entity {entity} {path} {data_type} {scale}")

    def store_success_entity(self, entity: Entity, path: str, data_type: str, scale: float | int) -> Self:
        return self._append_clause("store", f"store success entity {entity} {path} {data_type} {scale}")

    def store_result_storage(self, storage: str, path: str, data_type: str, scale: float | int) -> Self:
        return self._append_clause("store", f"store result storage {storage} {path} {data_type} {scale}")

    def store_success_storage(self, storage: str, path: str, data_type: str, scale: float | int) -> Self:
        return self._append_clause("store", f"store success storage {storage} {path} {data_type} {scale}")
    
    def run(self, command: Command):
        return self._append_clause("run", f"run {command!s}")

class ScoreboardCmd(Command):
    class Objectives:
        @staticmethod
        def add(objective: str, criteria: ScoreboardCriteria, display_name: str | None = None):
            """Creates a scoreboard objective."""
            return ScoreboardCmd(f"scoreboard objectives add {objective} {criteria} {"" if display_name is None else display_name}")
        
        @staticmethod
        def list():
            """Lists all existing objectives with their display names and criteria."""
            return ScoreboardCmd("scoreboard objectives list")
        
        @staticmethod
        def remove(objective: str):
            """Deletes the named objective from the scoreboard system. Data is deleted 
            from the objectives list and score holders' scores, and if it was on a display 
            list it is no longer displayed."""
            return ScoreboardCmd(f"scoreboard objectives remove {objective}")
    
    class Players:
        @staticmethod
        def enable(targets: ScoreHolder, objective: str):
            """
            Enables the target(s) to use the /trigger command on the specified objective. 
            This command accepts non-player entities, but only players are able to actually 
            use the /trigger command. Until this command has been run, players can't trigger 
            that objective. Using the /trigger command disables it again.
            Note that if any of the targets did not previously have a score for that scoreboard, 
            this command sets their score to 0.
            """
            
            return ScoreboardCmd(f"scoreboard players enable {targets} {objective}")
        
        def set(targets: ScoreHolder, objective: str, score: int):
            "Set the targets' scores in the given objective, overwriting any previous score."
            return ScoreboardCmd(f"scoreboard players set {targets} {objective} {score}")
        
        def add(targets: ScoreHolder, objective: str, score: int):
            """Increments the targets' scores in that objective by the given amount."""
            return ScoreboardCmd(f"scoreboard players add {targets} {objective} {score}")
        
        def remove(targets: ScoreHolder, objective: str, score: int):
            """Decrements the targets' scores in that objective by the given amount."""
            return ScoreboardCmd(f"scoreboard players remove {targets} {objective} {score}")
        
        def reset(targets: ScoreHolder, objective: str | None = None):
            """Deletes score or all scores for the targets. If <objective> is specified, 
            then only that objective is cleared. Otherwise, this applies to all objectives.
            
            Note that this does not merely set the scores to 0: it removes the targets from the 
            scoreboard system (or for the given objective) altogether.
            
            This also disables the target players' ability to use `/trigger` command (on the 
            given objective if specified).
            
            Running `scoreboard players reset *` will reset the scores of all players, while 
            `scoreboard players reset @a` will only reset the scores of players online.
            """
            
            return ScoreboardCmd(f"scoreboard players reset {targets}" + f" {objective}" if objective is not None else "")

class TellrawCmd(Command):
    def __init__(self, target_selector: Entity, text_component: TextComponent):
        self.target_selector = target_selector
        self.text_component = text_component
    
    def __str__(self):
        return f"tellraw {self.target_selector} {self.text_component}"

class TriggerCmd(Command):
    @staticmethod
    def add(trigger: str, n: int = 1):
        return TriggerCmd(f"trigger {trigger} add {n}")
    
    @staticmethod
    def set(trigger: str, n: int):
        return TriggerCmd(f"trigger {trigger} set {n}")

class DialogCmd(Command):
    """Shows or clear dialogs.
    """
    
    @staticmethod
    def show(target: TargetSelector, dialog: str):
        return DialogCmd(f"dialog show {target} {dialog}")
    
    @staticmethod
    def clear(target: TargetSelector):
        return DialogCmd(f"dialog clear {target}")

class ReturnCmd(Command):
    @staticmethod
    def return_(value: int):
        return ReturnCmd(f"return {value}")
    
    @staticmethod
    def fail():
        return ReturnCmd(f"return fail")
    
    @staticmethod
    def run(command: Command):
        return ReturnCmd(f"return run {command}")

class FunctionCmd(Command):
    @staticmethod
    def run(fn, args: NBTCompound | None = None):
        return FunctionCmd(f"function {fn} {args if args is not None else ""}")
    
    @staticmethod
    def with_entity(fn, entity: Entity, path: str):
        return FunctionCmd(f"function {fn} with entity {entity} {path if path is not None else ""}")
    
    @staticmethod
    def with_block(fn, blockpos: tuple[int | str, int | str, int | str], path: str):
        return FunctionCmd(f"function {fn} with storage {" ".join(blockpos)} {path if path is not None else ""}")
    
    @staticmethod
    def with_storage(fn, storage: str, path: str):
        return FunctionCmd(f"function {fn} with storage {storage} {path if path is not None else ""}")

class ItemCmd(Command):
    @staticmethod
    def modify_block(block_pos, slot, modifier: str):
        return ItemCmd(f"item modify block {block_pos} {slot} {modifier}")
    
    @staticmethod
    def modify_entity(entity: TargetSelector, slot, modifier: str):
        return ItemCmd(f"item modify entity {entity!s} {slot} {modifier}")

