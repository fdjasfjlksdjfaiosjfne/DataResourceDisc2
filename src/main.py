from pathlib import Path
from data import deinit, init
from zipfile import ZipFile, ZIP_DEFLATED
from hashlib import sha1
import logging

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

from data import DATA

if DATA.mode == "release":
    logger = logging.getLogger("disc_gen/zip")
    dist = root / "dist"
    for i in dist.glob("*.zip"):
        i.unlink()
    logger.info("Packing datapack...")
    zip_directory(DATA.paths.datapack, dist / f"Disc_Datapack_Thing_Ver_{DATA.common_version}_{DATA.specific_version.datapack}.zip")
    logger.info("Packing resource pack...")
    zip_directory(DATA.paths.respack, dist / f"Disc_Art_Additions_Ver_{DATA.common_version}_{DATA.specific_version.respack}.zip")
    logger.info("Packing sound pack...")
    SOUND_PACK = dist / f"Disc_Cores_Ver_{DATA.common_version}.zip"
    zip_directory(DATA.paths.soundpack, SOUND_PACK)
    logger.info("Hashing sound pack...")
    print("Sound pack hash:", sha1_file(SOUND_PACK))

deinit(root / "data/data.json5")