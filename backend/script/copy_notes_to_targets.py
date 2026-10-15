#!/usr/bin/env python3
"""Copy generated notes into the per-source target directories from temp.txt.

temp.txt line format (added by the user):
    <TARGET_DIR>  <label>  <space/list URL>  <requirements>

For every source (goal_videos/<label>.txt) we take each successfully generated
video note (backend/note_results/<task_id>_markdown.md) and copy it into
<TARGET_DIR>/<video title>.md, using the real video title from the task's
audio_meta.

Run from backend/:
    python script/copy_notes_to_targets.py --dry-run
    python script/copy_notes_to_targets.py
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
GOAL = ROOT / "goal_videos"
NOTE_DIR = BACKEND / "note_results"
DB = BACKEND / "bili_note.db"
PROGRESS = GOAL / "_goal_notes_progress.jsonl"
SKIP = GOAL / "_goal_notes_skip.txt"
MAX_TITLE = 100

_INVALID = {
    "/": "／", "\\": "＼", ":": "：", "*": "＊", "?": "？",
    '"': "＂", "<": "＜", ">": "＞", "|": "｜",
}


def bv_of(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1].split("?")[0]


def norm_label(s: str) -> str:
    return s.strip().rstrip("-").strip()


def sanitize(title: str) -> str:
    t = "".join(_INVALID.get(c, c) for c in title)
    t = "".join(c for c in t if c >= " " or c == "\t")  # drop control chars
    t = re.sub(r"\s+", " ", t).strip().rstrip(". ")
    if len(t) > MAX_TITLE:
        t = t[:MAX_TITLE].rstrip(". ")
    return t or "untitled"


def parse_targets() -> dict[str, str]:
    """label(normalised) -> target directory (as written in temp.txt)."""
    out: dict[str, str] = {}
    for line in (GOAL / "temp.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        target = parts[0]
        url_idx = next((i for i, p in enumerate(parts) if p.startswith("http")), None)
        label_parts = parts[1:url_idx] if url_idx else parts[1:]
        label = norm_label(" ".join(label_parts)) or norm_label(Path(target).name)
        out[label] = target
    return out


def source_files() -> list[Path]:
    skip = {"temp.txt"}
    return sorted(
        p for p in GOAL.glob("*.txt")
        if p.name not in skip and not p.name.startswith("_")
    )


def task_id_candidates() -> dict[str, list[str]]:
    """BV -> [task_id, ...] from the DB (successful saves) and the run progress."""
    cands: dict[str, list[str]] = {}

    def add(bv, tid):
        if bv and tid and tid not in cands.setdefault(bv, []):
            cands[bv].append(tid)

    try:
        con = sqlite3.connect(DB)
        for vid, tid in con.execute("SELECT video_id, task_id FROM video_tasks"):
            if vid and tid:
                add(vid, tid)
        con.close()
    except Exception as e:  # pragma: no cover
        print(f"[warn] db read failed: {e}", file=sys.stderr)

    if PROGRESS.exists():
        for ln in PROGRESS.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if r.get("status") == "SUCCESS":
                add(r.get("bv"), r.get("task_id"))
    return cands


def pick_task(bv: str, cands: dict[str, list[str]]) -> tuple[str | None, Path | None]:
    for tid in cands.get(bv, []):
        md = NOTE_DIR / f"{tid}_markdown.md"
        if md.exists():
            return tid, md
    return None, None


def title_for(tid: str, bv: str) -> str:
    for name in (f"{tid}.json", f"{tid}_audio.json"):
        p = NOTE_DIR / name
        if not p.exists():
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        am = d.get("audio_meta") if isinstance(d.get("audio_meta"), dict) else d
        title = am.get("title") if isinstance(am, dict) else None
        if title:
            return str(title)
    return bv


def main() -> int:
    ap = argparse.ArgumentParser(description="Copy notes into temp.txt target dirs, named by video title")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="", help="only sources whose label contains this substring")
    args = ap.parse_args()

    targets = parse_targets()
    srcs = source_files()
    cands = task_id_candidates()

    total_copied = total_missing = 0
    for src in srcs:
        label = norm_label(src.stem)
        if args.only and args.only not in label:
            continue
        target = targets.get(label)
        if not target:
            print(f"[skip] no target dir for source '{label}'", file=sys.stderr)
            continue

        urls = [l.strip() for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
        bvs = [bv_of(u) for u in urls]
        skipped = set()
        if SKIP.exists():
            skipped = {l.strip() for l in SKIP.read_text(encoding="utf-8").splitlines()
                       if l.strip() and not l.lstrip().startswith("#")}

        outdir = Path(target)
        copied = missing = 0
        used: dict[str, str] = {}
        for bv in bvs:
            if bv in skipped:
                continue
            tid, md = pick_task(bv, cands)
            if not md:
                missing += 1
                continue
            base = sanitize(title_for(tid, bv))
            name = f"{base}.md"
            if name in used and used[name] != bv:
                n = 2
                while f"{base} ({n}).md" in used:
                    n += 1
                name = f"{base} ({n}).md"
            used[name] = bv
            dst = outdir / name
            if args.dry_run:
                if copied < 3:
                    print(f"  [{label}] {bv} -> {dst}")
            else:
                outdir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(md, dst)
            copied += 1
        total_copied += copied
        total_missing += missing
        print(f"{'DRY ' if args.dry_run else ''}{label}: copied={copied} missing_note={missing} -> {target}")

    print(f"\n{'DRY-RUN ' if args.dry_run else ''}TOTAL copied={total_copied} missing_note={total_missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
