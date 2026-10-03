from typing import Final
from ..paths.datapack import Data
from ..raw import NS
from ..writers import BaseFileWriter
from ...core import Command

class Function(BaseFileWriter):
    def __init__(self, namespace: str, name: str, *commands: Command):
        self.namespace = namespace
        self.name = name
        self.path = Data / ""
    def write(self):
        

InfoFn: Final = Function(
    NS, "info"
)

