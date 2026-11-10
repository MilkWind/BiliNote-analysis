#!/usr/bin/env python3
"""Inject a `> 来源链接：<url>` header into notes copied into the knowledge base.

The v2 copies were byte-verbatim, so they carry no provenance. This adds the
Bilibili URL of the source video to each note, matching the existing KB style:

  * notes that start with an H1   -> `# Title`, blank line, then the link
  * notes that start with content -> link on the very first line, blank line

Multi-part videos keep their `?p=N` suffix so the link points at the right part.

Idempotent: a note already containing `来源链接` is left alone. Files are
re-written with CRLF line endings, like the rest of the knowledge base.

Placement
---------
* Note starting with an H1 -> blank line, `> 来源链接：…`, blank line, then content.
* Otherwise the link becomes the first line, followed by a blank line.

The URL comes from the progress log (`url`, which keeps `?p=N` for parts), with
orphan notes resolved from their task JSON. It reads the path of each note from
`goal_videos/_kb_copy_state.json`, so **run `copy_notes_to_kb_v2.py` first**.

Usage (from backend/):
    python script/inject_source_links.py --dry-run
    python script/inject_source_links.py
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
GOAL = ROOT / "goal_videos"
PROGRESS = GOAL / "_goal_notes_progress_v2.jsonl"
STATE = GOAL / "_kb_copy_state.json"
KB_NOTES = Path(r"D:\development-projects\personal-projects\persional-knowledge\notes")
REPORT = GOAL / "_kb_source_link_report.md"

sys.path.insert(0, str(BACKEND / "script"))
import copy_notes_to_kb_v2 as copy_v2  # noqa: E402

HEADER_PREFIX = "> 来源链接："
MARKER = "来源链接"


def video_urls() -> dict[str, str]:
    """video_id -> source URL, from the progress log and orphan notes."""
    urls: dict[str, str] = {}
    known: list[dict] = []
    for line in PROGRESS.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if rec.get("status") != "SUCCESS":
            continue
        vid = rec.get("video_id")
        if vid and rec.get("url"):
            urls[vid] = rec["url"]
            known.append(rec)
    for rec in copy_v2.orphan_records(known):
        vid = rec.get("video_id")
        if vid and vid not in urls and rec.get("url"):
            urls[vid] = rec["url"]
    return urls


def insert_link(text: str, url: str) -> str:
    """Return text with the link header added, preserving the original line style."""
    crlf = "\r\n" in text
    lines = text.replace("\r\n", "\n").split("\n")
    link = f"{HEADER_PREFIX}{url}"

    # Keep leading blank lines out of the way when deciding placement.
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    if idx < len(lines) and lines[idx].startswith("# "):
        # Blank line between the H1 and the link, then a blank line before content.
        lines.insert(idx + 1, "")
        lines.insert(idx + 2, link)
        if idx + 3 < len(lines) and lines[idx + 3].strip():
            lines.insert(idx + 3, "")
    else:
        lines.insert(idx, link)
        lines.insert(idx + 1, "")

    out = "\n".join(lines)
    return out.replace("\n", "\r\n") if crlf else out


def main() -> int:
    ap = argparse.ArgumentParser(description="Add source links to KB notes")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    state = json.loads(STATE.read_text(encoding="utf-8"))
    urls = video_urls()
    items = sorted(state.items())
    if args.limit:
        items = items[: args.limit]

    added = already = missing_file = no_url = 0
    no_url_ids: list[str] = []
    for vid, rel in items:
        path = KB_NOTES / rel
        if not path.exists():
            missing_file += 1
            continue
        url = urls.get(vid)
        if not url:
            no_url += 1
            no_url_ids.append(vid)
            continue
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig", errors="replace")
        if MARKER in text[:300]:
            already += 1
            continue
        new = insert_link(text, url)
        if not args.dry_run:
            path.write_bytes(new.encode("utf-8"))
        added += 1

    lines = [
        "# KB source-link report",
        "",
        f"- mode: {'dry-run' if args.dry_run else 'write'}",
        f"- state entries: {len(items)}",
        f"- link added: {added}",
        f"- already had a link: {already}",
        f"- missing file: {missing_file}",
        f"- no source url: {no_url}",
    ]
    if no_url_ids:
        lines += ["", "## without a source URL", ""] + [f"- {v}" for v in no_url_ids[:50]]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"entries={len(items)} added={added} already={already} "
          f"missing_file={missing_file} no_url={no_url}")
    print(f"report: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
