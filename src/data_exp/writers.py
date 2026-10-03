from abc import ABC
from enum import Enum, auto
import json, json5
from ...loggers import Writers as logger
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from .. import BaseDataclass
from ...core import Command

class MyJSONDecoder(json.JSONDecoder, json5.JSON5Encoder):
    def default(self, obj):
        if isinstance(obj, Command):
            return obj.build()
        if isinstance(obj, BaseDataclass):
            ...
        return super().default()

class FileWriterType(Enum):
    DeserializeJSON = auto()
    DeserializeJSON5 = auto()
    String = auto()
    CmdList = auto()
    CopyFromPath = auto()

class BaseFileWriter(ABC):
    def write(self): ...

class FileWriter:
    def __init__(self, path: Path, type: FileWriterType, content):
        """The internal initializer for `FileWriter`.
        
        In most cases, you should probably use one of the other initializer methods instead
        (`deserialize_json(path, content)`)
        """
        self.path = path
        self.type = type
        self.content = content
    
    @classmethod
    def deserialize_json(cls, path: Path, content: Any):
        try:
            return cls(path, FileWriterType.DeserializeJSON, json.dumps(content))
        except json.JSONDecodeError as e:
            logger.error("The object '{!r} cannot be serialize to JSON. Exception below:\n{}'", content, e)
            return cls(path, FileWriterType.String, content)
    
    @classmethod
    def deserialize_json5(cls, path: Path, content: Any):
        try:
            return cls(path, FileWriterType.DeserializeJSON5, json.dumps(content))
        except json.JSONDecodeError as e:
            logger.error("The object '{!r} cannot be serialize to JSON5. Exception below:\n{}'", content, e)
            return cls(path, FileWriterType.String, content)
    
    @classmethod
    def plain_string(cls, path: Path, content: str):
        return cls(path, FileWriterType.String, content)
    
    @classmethod
    def cmd_list(cls, path: Path, content: list[Command]):
        return cls(path, FileWriterType.CmdList, content)
    
    @classmethod
    def copy_from_path(cls, path: Path, content: Path):
        return cls(path, FileWriterType.CopyFromPath)
    
    def write(self):
        self.path.parent.mkdir(parents = True, exist_ok = True)
        match self.type:
            case FileWriterType.DeserializeJSON:
                with self.path.open("r") as f:
                    json.dump(self.content, f, cls = MyJSONDecoder)
            case FileWriterType.DeserializeJSON5:
                with self.path.open("r") as f:
                    json5.dump(self.content, f, cls = MyJSONDecoder)
            case FileWriterType.String:
                self.path.write_text(self.content)
            case FileWriterType.CmdList:
                self.path.write_text(i.build() for i in cast(list[Command], self.content))
            case FileWriterType.CopyFromPath:
                cast(Path, self.content).parent.mkdir(parents = True, exist_ok = True)
                self.path.copy_into(self.content)