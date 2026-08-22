from pathlib import Path
from pydub import AudioSegment

OVERRIDE_ALL = False
COMPRESS = True

music_folder = Path(__file__).parent
dist = music_folder / "dist"

for path in music_folder.glob("*.ogg"):
    if OVERRIDE_ALL or not (dist / path.name).exists():
        AudioSegment.from_ogg(path).export(
            dist / path.name,
            format = "ogg",
            codec = "libvorbis",
            bitrate = "92k" if COMPRESS else None,
            parameters =
                # Quality, 5 is high quality
                (["-q:a", "4"] if COMPRESS else []) +
                # Force override
                ["-y"]
        )