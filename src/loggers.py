"""Utilities containing various utilities for loggers."""
from abc import ABC
from enum import Enum, auto
from typing import Any, Callable, Final, Literal
from rich.text import Text
from rich.style import Style
import functools

from core import OurConsole, singleton

class LogAction(ABC):
    def after_log(self) -> Any: ...

@singleton
class Continue(LogAction):
    def after_log(self):
        pass

class Pause(LogAction):
    def __init__(self, prompt: str | None = None):
        self.prompt = prompt
    def after_log(self) -> None:
        if self.prompt is not None:
            OurConsole.print(self.prompt)
        OurConsole.input("[blue]Press Enter to continue...")

class AskForConfirmation(LogAction):
    def __init__(self, prompt: str | Text, *, 
                 default: Literal["y", "n", "Y", "N"],
                 on_yes: Callable[[], None] | None = None, 
                 on_no: Callable[[], None] | None = None):
        self.prompt = Text(prompt) if isinstance(prompt, str) else prompt
        self.default = default
        self.on_yes = on_yes
        self.on_no = on_no
    def after_log(self) -> bool:
        def conv(v: Literal["y", "n", "Y", "N"]): return v.lower() == "y"
        y = "Y" if self.default.lower() == "y" else "y"
        n = "N" if self.default.lower() == "n" else "n"
        answer = OurConsole.input(
            self.prompt + " "
            + Text("[", style = Style(color = "grey0"))
            + Text(y, style = Style(color = "green"))
            + Text("/", style = Style(color = "grey0"))
            + Text(n, style = Style(color = "red"))
            + Text("]", style = Style(color = "grey0"))
            + Text(": ", style = Style(color = "grey0"))
        )
        result = conv(answer) if answer in {"y", "n", "Y", "N"} else conv(self.default)
        if result and self.on_yes is not None:
            self.on_yes()
        elif (not result) and self.on_no is not None:
            self.on_no()
        return result

AskToContinue: Final = AskForConfirmation(
    Text("Are you sure you want to continue?", style = Style(color = "yellow")), default = "N",
    on_no = lambda: exit(1)
)

@singleton
class Exit(LogAction):
    def after_log(self):
        exit(1)

class AskForContent(LogAction):
    def __init__(self, prompt: str | Text, password: bool = False):
        self.prompt = prompt
        self.password = password
    def after_log(self):
        return OurConsole.input(self.prompt, password = self.password)

class LevelInfo:
    def __init__(self, level: int, color, action: LogAction = Continue):
        self.level = level
        self.color = color
        self.action = action

@functools.total_ordering
class Level(Enum):
    """
    Contains different levels of logging.
    - `Debug` (10): Contains debugging information.
    - `Info` (20): Contains general info
    - `Note` (25): Add a minor foretold that you can ignore.
Either used as a highlighted `Info` or a `Warn` without any 
consequences or much urgency.
    - `Warn` (30): A warning that asks for attention, but the
script can try to recover gracefully from it. The script is paused.
    - `Error` (40): You fuck up. The script is paused here.
    - `Critical` (50): You fuck up extremely bad. Automatically 
closes itself the second this log is emitted.
    """ 
    
    # :skull:
    Debug = LevelInfo(10, "bright_black")
    Info = LevelInfo(20, "blue")
    Note = LevelInfo(25, "green")
    Warn = LevelInfo(30, "yellow", AskToContinue)
    Error = LevelInfo(40, "gold", AskToContinue)
    Critical = LevelInfo(50, "bold bright_red", Exit)
    def __lt__(self, other: Level):
        return self.value.level < other.value.level
    def __eq__(self, other: Level):
        if isinstance(other, Level):
            return self.value.level == other.value.level
        return super().__eq__()
    def __ne__(self, other): return not(self == other)

CurrentLevel: Final = Level.Info
LogFormat: Final = "[{style}]\\[{path}] {level}: {msg}"

class Logger:
    """A custom logger, which provides...maybe one or two extra pieces of functionality.
    
    It's less of a logger now. More like, 
    """
    def __init__(self, path: str):
        self.path = path
        self.format = LogFormat
    def log(self, level: Level, msg: str, *args: Any, action: LogAction = None) -> Any:
        if CurrentLevel > level:
            return
        OurConsole.print(self.format.format(
            style = level.value.color,
            path = self.path,
            level = level.name.upper(),
            msg = msg.format(*args)
        ))
        
        if action is None:
            action = level.value.action
        return action.after_log()

    def debug(self, msg: str, *args: Any, action: LogAction = None):
        return self.log(Level.Debug, msg, *args, action = action)
    def info(self, msg: str, *args: Any, action: LogAction = None):
        return self.log(Level.Info, msg, *args, action = action)
    def note(self, msg: str, *args: Any, action: LogAction = None):
        return self.log(Level.Note, msg, *args, action = action)
    def warn(self, msg: str, *args: Any, action: LogAction = None):
        return self.log(Level.Warn, msg, *args, action = action)
    def error(self, msg: str, *args: Any, action: LogAction = None):
        return self.log(Level.Error, msg, *args, action = action)
    def critical(self, msg: str, *args: Any, action: LogAction = None):
        return self.log(Level.Critical, msg, *args, action = action)

Namespace: Final = "pack_gen"
Respack: Final = Logger(f"{Namespace}/respack")
Datapack: Final = Logger(f"{Namespace}/datapack")
Writers: Final = Logger(f"{Namespace}/data/writer")
Commands: Final = Logger(f"{Namespace}/commands")
MCObjects: Final = Logger(f"{Namespace}/mc_objects")
Discs: Final = Logger(f"{Namespace}/data/discs")