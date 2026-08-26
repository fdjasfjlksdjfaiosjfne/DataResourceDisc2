from pathlib import Path
from data import init
from zipfile import ZipFile, ZIP_DEFLATED
from hashlib import sha1
import logging
import sys

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

root = Path(__file__).parent.parent

logging.basicConfig(
    level = logging.INFO,
    format = "[%(name)s] %(levelname)s: %(message)s"
)

init(
    data_jsons = [
        root / "data/data.json5",
        root / "data/data.json"
    ]
)

import datapack, respack
datapack.init()
respack.init()

# import src.datapack as datapack, src.respack as respack
# datapack.init()
# respack.init()
# if CONFIG.is_release_mode():
#     dist = Path(__file__).parent / "dist"
#     print("Packing datapack...")
#     zip_directory(CONFIG.debug_datapack_path(), dist / f"Disc_Datapack_Thing_Ver_{CONFIG.version()}.zip")
#     print("Packing resource pack...")
#     zip_directory(CONFIG.debug_respack_path(), dist / f"Disc_Art_Additions_Ver_{CONFIG.version()}.zip")
#     print("Packing sound pack...")
#     SOUND_PACK = dist / f"Disc_Cores_Ver_{CONFIG.version()}.zip"
#     zip_directory(CONFIG.debug_soundpack_path(), SOUND_PACK)
#     print("Hashing sound pack...")
#     print("Sound pack hash:", sha1_file(SOUND_PACK))