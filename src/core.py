"""This file contains:
- Classes that are commonly referenced by other modules, before its 
corresponding module actually initializes. This is mainly used to 
prevent circular imports.
- Common things that don't make sense anywhere else and do not warrant 
an extra file. Critically, they *do not* require any other file except for 
dependencies (e.g. `json`, `json5`, `rich`)

Note: They are all functional class. They are functionally identical
to where the class would have been.
```
>>> import core, command
>>> assert core.Command is command.Command
```
"""


from abc import ABC
from typing import Final, Protocol

from rich.console import Console

OurConsole: Final = Console()

true = True
false = False
null = None

type BasicDataType = dict[str, BasicDataType] | list[BasicDataType] | int | float | str
class Serializable(ABC):
    def serialize(self) -> BasicDataType:
        pass

def singleton[T](cls: type[T]) -> T:
    """Takes a class, instantiate it (with no arguments), and then replace the object in its place.
    
    Intended to replicate Kotlin's `object` declaration. 
    
    (All this does is calling the class btw.)
    """
    return cls()

def to_camel_case(s: str) -> str:
    "Converts a `snake_case` string to `camelCase`"
    parts = s.replace("-", "_").split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])

class Command(Serializable):
    """The base class for command classes.
    
    This class in particular simply store a string 
    and return it when building the string.
    """
    
    def __init__(self, command: str):
        "Takes in a raw string as a command."
        self._command = command
    def __str__(self): return self.build()
    def build(self):
        """Returns a usable version of the command (without the `/`).
        
        Does the same thing as `str(self)`.
        
        Override this method if you wish to modify the parsing behavior.
        """
        return self._command.strip()
    def serialize(self) -> str:
        return self.build()