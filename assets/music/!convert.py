from pathlib import Path
from pydub import AudioSegment
from itertools import chain

# Change this to `true` if you want to delete the original files
DELETE_OLD = False
EXTENSIONS = ["mp3", "wav", "flac", "mp4"]
music_folder = Path(__file__).parent

for path in chain(*[music_folder.glob(f"*.{ext}") for ext in EXTENSIONS]):
    AudioSegment.from_file(path).export(
        music_folder / (path.stem + ".ogg"),
        format = "ogg",
        codec = "libvorbis",
        parameters = [
            # Maintain high quality
            "-q:a", " 5",
            # Take in only audio streams from the input
            "-map", "0:a"
        ]
    )
    if DELETE_OLD and path.suffix != ".ogg":
        path.unlink()