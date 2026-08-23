from pathlib import Path
import json
from config import Config
from zipfile import ZipFile, ZIP_DEFLATED
from hashlib import sha1

def zip_directory(source: Path, destination: Path):
    with ZipFile(destination, "w", compression = ZIP_DEFLATED, compresslevel = 9) as zip:
        for file in source.rglob("*"):
            if file.is_file():
                zip.write(file, file.relative_to(source))

def sha1_file(path: Path) -> str:
    hasher = sha1()

    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)

    return hasher.hexdigest()

with open(Path(__file__).parent / "data.json", encoding = "utf-8") as f:
    print("Initializing config...")
    CONFIG = Config(json.load(f))

# Check for duplicated IDs
a = []
b = []
print("Checking for duplicated IDs...")
for i in CONFIG.disc_index():
    if i.id in a:
        raise ValueError(f"Duplicated ID: {i.id}")
    if i.config_id in b:
        raise ValueError(f"Duplicated config ID: {i.config_id}")
    a.append(i.id)
    b.append(i.config_id)

if not (Path(__file__).parent / "textures/missing.png").exists():
    print("\\e[0;91mmissing.png does not exist. The generator does not have a failsafe for this and will crash if it is needed.\\e[0m")

import datapack, respack
datapack.init()
respack.init()
if CONFIG.is_release_mode():
    dist = Path(__file__).parent / "dist"
    print("Packing datapack...")
    zip_directory(CONFIG.debug_datapack_path(), dist / f"Disc Datapack Thing [Ver 1.{CONFIG.version()}].zip")
    print("Packing resource pack...")
    zip_directory(CONFIG.debug_respack_path(), dist / f"Disc Art Additions [Ver {CONFIG.version()}].zip")
    print("Packing sound pack...")
    SOUND_PACK = dist / f"Disc's Cores [Ver {CONFIG.version()}].zip"
    zip_directory(CONFIG.debug_soundpack_path(), SOUND_PACK)
    print("Hashing sound pack...")
    print("Sound pack hash:", sha1_file(SOUND_PACK))