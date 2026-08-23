from pathlib import Path

try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None

MUSIC_DIR = Path(__file__).parent.parent / "assets/music"

def move_and_compress(id: str):
    if AudioSegment is None:
        raise ImportError('pydub not exist')