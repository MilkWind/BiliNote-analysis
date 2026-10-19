#!/usr/bin/env python3
"""Copy 程序员方格 notes into a categorized knowledge-base directory.

Source:  goal_videos/程序员方格_笔记/<category>/<NNN> <分P title>.md
Target:  <target>/<category>/<分P title>.md

The numeric ordering prefix is removed so each file is named exactly after its
分P title (sanitised for Windows). Notes are matched by URL through the batch
progress file, so a later re-classification does not break the mapping.

Missing notes (the two silent-audio parts) are skipped and reported.

Usage (run from backend/):
    python script/copy_programmer_fangge_notes.py --dry-run
    python script/copy_programmer_fangge_notes.py --clean
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
GOAL = ROOT / "goal_videos"
CLASS_JSON = GOAL / "程序员方格_分P分类.json"
SRC_ROOT = GOAL / "程序员方格_笔记"
PROGRESS = GOAL / "_programmer_fangge_progress.jsonl"
DEFAULT_TARGET = Path(
    r"D:\development-projects\personal-projects\persional-knowledge"
    r"\notes\technology\fullstack\frontend\程序员方格"
)

_INVALID = {
    "/": "／", "\\": "＼", ":": "：", "*": "＊", "?": "？",
    '"': "＂", "<": "＜", ">": "＞", "|": "｜",
}


def sanitize(title: str, limit: int = 100) -> str:
    t = "".join(_INVALID.get(c, c) for c in title)
    t = "".join(c for c in t if c >= " " or c == "\t")
    t = re.sub(r"\s+", " ", t).strip().rstrip(". ")
    if len(t) > limit:
        t = t[:limit].rstrip(". ")
    return t or "untitled"


def success_note_paths() -> dict[str, Path]:
    """url -> latest existing note markdown, from the batch progress file."""
    out: dict[str, Path] = {}
    if not PROGRESS.exists():
        return out
    for line in PROGRESS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        if rec.get("status") != "SUCCESS":
            continue
        note = rec.get("note_path")
        if not note:
            continue
        p = ROOT / note
        if p.exists():
            out[rec["url"]] = p
    return out


def source_index() -> dict[str, Path]:
    """sanitised 分P title -> source note, as a fallback when progress is missing."""
    index: dict[str, Path] = {}
    if not SRC_ROOT.exists():
        return index
    for p in SRC_ROOT.rglob("*.md"):
        stem = re.sub(r"^\d{3} ", "", p.stem)
        stem = re.sub(r" \(\d+\)$", "", stem)
        index.setdefault(stem, p)
    return index


def main() -> int:
    ap = argparse.ArgumentParser(description="Copy notes into categorized KB dirs")
    ap.add_argument("--target", default=str(DEFAULT_TARGET))
    ap.add_argument("--clean", action="store_true", help="remove existing category dirs first")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    target = Path(args.target)
    data = json.loads(CLASS_JSON.read_text(encoding="utf-8"))
    by_url = success_note_paths()
    by_title = source_index()

    slugs = {c["slug"] for c in data["categories"]}
    if args.clean and not args.dry_run and target.exists():
        for d in target.iterdir():
            if d.is_dir() and d.name in slugs:
                shutil.rmtree(d)

    copied = missing = renamed = 0
    missing_items: list[str] = []
    used: dict[Path, str] = {}

    for cat in data["categories"]:
        slug = cat["slug"]
        dst_dir = target / slug
        if not args.dry_run:
            dst_dir.mkdir(parents=True, exist_ok=True)

        for item in cat["items"]:
            title = item["title"]
            src = by_url.get(item["url"]) or by_title.get(sanitize(title))
            if not src or not src.exists():
                missing += 1
                missing_items.append(f"{slug} {title}")
                continue

            base = sanitize(title)
            dst = dst_dir / f"{base}.md"
            n = 2
            while dst in used:
                dst = dst_dir / f"{base} ({n}).md"
                n += 1
            used[dst] = item["url"]

            if dst.name != src.name:
                renamed += 1
            if args.dry_run:
                if copied < 8:
                    print(f"{src.relative_to(ROOT)}  ->  {dst}")
            else:
                shutil.copy2(src, dst)
            copied += 1

    print(
        f"{'DRY-RUN ' if args.dry_run else ''}copied={copied} "
        f"missing={missing} renamed={renamed} target={target}"
    )
    if missing_items:
        print("missing notes:", file=sys.stderr)
        for line in missing_items:
            print("  " + line, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
