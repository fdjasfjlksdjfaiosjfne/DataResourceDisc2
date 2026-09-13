from pathlib import Path
from commands import CommandSyntaxException
from data import deinit, init
from zipfile import ZipFile, ZIP_DEFLATED
from hashlib import sha1
import logging
import sys
import traceback

def excepthook(exc_type, exc, tb):
    if isinstance(exc, CommandSyntaxException):
        print(exc.source)
        print(" " * exc.position[0] + "^" * (exc.postion[1] - exc.position[0]))
        print(f"{exc_type.__name__}: {exc}")
        print()
        traceback.print_tb(tb)
    else:
        sys.__excepthook__(exc_type, exc, tb)

sys.excepthook = excepthook

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
    level = logging.DEBUG,
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
    zip_directory(DATA.paths.datapack, dist / f"Discs_Shells_Ver_{DATA.common_version}_{DATA.specific_version.datapack}.zip")
    logger.info("Packing resource pack...")
    zip_directory(DATA.paths.respack, dist / f"Discs_Souls_Ver_{DATA.common_version}_{DATA.specific_version.respack}.zip")
    logger.info("Resource pack SHA-1: %s", sha1_file(dist / f"Discs_Souls_Ver_{DATA.common_version}_{DATA.specific_version.respack}.zip"))

deinit(root / "data/data.json5")