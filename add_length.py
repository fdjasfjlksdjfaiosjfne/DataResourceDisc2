"""
This file is for adding a 'length' field for any song information in 
`data.json`, that doesn't have one yet.
"""

from pydub import AudioSegment
from pathlib import Path
import json

DATA_JSON = Path(__file__).parent / "data.json"

with open(DATA_JSON, encoding="utf-8") as f:
    d = json.load(f)

with open(DATA_JSON, "w", encoding="utf-8") as f:
    new = []
    for spec in d["discs_index"]:
        if "length" in spec:
            new.append(spec)
            continue
        print(f"Processing length for {spec["id"]}...")
        segment = AudioSegment.from_ogg(Path(__file__).parent / f"music/{spec["id"]}.ogg")
        new.append(spec | {
            "length": len(segment) / 1000
        })
    d["discs_index"] = new
    json.dump(d, f, indent=4, ensure_ascii=False)