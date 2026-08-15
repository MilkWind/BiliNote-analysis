#!/usr/bin/env python3
"""Copy each generated note markdown into the knowledge base, named by its 分P title."""
import json
import re
import sys
from pathlib import Path

NOTE_DIR = Path("note_results")
TARGET = Path(r"D:\development-projects\personal-projects\persional-knowledge\technology\fullstack\mobile\react-native")

BAD_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def sanitize(name: str) -> str:
    name = BAD_CHARS.sub("_", name)
    name = name.strip().rstrip(".")
    return name or "unnamed"


def part_name(title: str, video_id: str) -> str:
    m = re.search(r"p(\d+)\s+(.+)$", title)
    if m:
        return m.group(2).strip()
    m2 = re.search(r"_p(\d+)$", video_id)
    return f"p{m2.group(1)}" if m2 else video_id


TARGET.mkdir(parents=True, exist_ok=True)
copied = []
missing = []
for audio in sorted(NOTE_DIR.glob("*_audio.json")):
    data = json.loads(audio.read_text(encoding="utf-8"))
    video_id = data.get("video_id", "")
    title = data.get("title", "")
    pn = re.search(r"_p(\d+)$", video_id)
    if not pn:
        missing.append(f"{audio.name}: no pN in video_id {video_id!r}")
        continue
    markdown = NOTE_DIR / (audio.stem.replace("_audio", "_markdown.md"))
    if not markdown.exists():
        missing.append(f"{audio.name}: no markdown for {markdown.name}")
        continue
    name = f"{int(pn.group(1)):02d}_{sanitize(part_name(title, video_id))}.md"
    dst = TARGET / name
    dst.write_bytes(markdown.read_bytes())
    copied.append(f"{video_id} -> {name}")

print(f"copied: {len(copied)}")
for line in sorted(copied):
    print(line)
if missing:
    print("MISSING:")
    for line in missing:
        print(line)
    sys.exit(1)
