from typing import Final

from . import CodebaseRoot

Assets: Final = CodebaseRoot / "assets"
MusicFiles: Final = Assets / "music/dist"
Textures: Final = Assets / "textures"
DiscTextures: Final = Textures / "discs"
XPTomeTextures: Final = Textures / "xp_tomes"