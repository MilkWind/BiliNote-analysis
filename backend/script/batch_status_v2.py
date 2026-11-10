#!/usr/bin/env python3
"""Read-only progress snapshot for the batch in ``goal_videos/_goal_notes_progress_v2.jsonl``.

Answers "where is the batch right now?" without touching the running driver.

Shows
-----
* total records / unique videos, SUCCESS and FAILED counts
* how many tasks the backend currently has in flight (read from
  ``note_results/*.status.json``)
* the timestamp of the first and last success (for computing throughput)
* a per-source SUCCESS / FAILED / total breakdown

Usage (from backend/):
    python script/batch_status_v2.py

Safe to run at any time, including mid-batch: it only reads files.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
GOAL = ROOT / "goal_videos"
PROGRESS = GOAL / "_goal_notes_progress_v2.jsonl"
NOTE_DIRS = [BACKEND / "note_results", ROOT / "note_results"]
ACTIVE = {"PENDING", "PARSING", "DOWNLOADING", "TRANSCRIBING",
          "SUMMARIZING", "FORMATTING", "SAVING", "RUNNING"}


def main() -> int:
    records: list[dict] = []
    if PROGRESS.exists():
        for ln in PROGRESS.read_text(encoding="utf-8").splitlines():
            try:
                records.append(json.loads(ln))
            except Exception:
                pass

    # Latest record per video_id wins.
    latest: dict[str, dict] = {}
    for r in records:
        vid = r.get("video_id") or r.get("url") or ""
        latest[vid] = r

    by_status = Counter(r.get("status") for r in latest.values())
    by_source: dict[str, Counter] = defaultdict(Counter)
    for r in latest.values():
        by_source[r.get("source", "?")][r.get("status", "?")] += 1

    active = Counter()
    for d in NOTE_DIRS:
        if not d.exists():
            continue
        for f in d.glob("*.status.json"):
            if f.name.endswith("_markdown.status.json"):
                continue
            try:
                s = json.loads(f.read_text(encoding="utf-8")).get("status")
                if s in ACTIVE:
                    active[s] += 1
            except Exception:
                pass

    successes = [r for r in latest.values() if r.get("status") == "SUCCESS"]
    print(f"records={len(records)} unique={len(latest)} "
          f"SUCCESS={by_status.get('SUCCESS', 0)} FAILED={by_status.get('FAILED', 0)}")
    print(f"active: {dict(active) or 'none'}")
    if successes:
        ts = sorted(r.get("ts", "") for r in successes if r.get("ts"))
        if ts:
            print(f"first success={ts[0]} last success={ts[-1]}")
    print("\nper source (SUCCESS/FAILED/total):")
    for source in sorted(by_source):
        c = by_source[source]
        print(f"  {source}: {c.get('SUCCESS', 0)}/{c.get('FAILED', 0)}/{sum(c.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
