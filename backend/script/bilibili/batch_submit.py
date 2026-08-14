#!/usr/bin/env python3
"""Sequentially generate notes for every remaining video in goal_videos/渡一.txt.

Safety properties (why this exists):
- The backend's /generate_note schedules a background task that BLOCKS a threadpool
  thread for the full ~90s note generation, and the serial executor runs 3 concurrent
  downloads. Rapid submission exhausts FastAPI's threadpool (server hangs) and triggers
  bilibili 412 rate-limiting. So we submit ONE task, wait for it to reach a terminal
  state, then submit the next.

Dedup / resume:
- Skips videos whose BV id already has a SUCCESS row in the DB (bili_note.db / video_task).
- Skips URLs recorded in goal_videos/渡一_done.txt (previous runs of this script).
- Before starting, waits for any already-queued tasks (from a prior burst) to drain.
"""
import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "http://localhost:8483/api/generate_note"
# These files' name are dynamic in different video understanding tasks.
INPUT = Path("../goal_videos/渡一.txt")
DONE = Path("../goal_videos/渡一_done.txt")
FAILED = Path("../goal_videos/渡一_failed.txt")
DB = Path("bili_note.db")
NOTE_DIR = Path("note_results")

ACTIVE_STATUSES = {"PENDING", "RUNNING", "PARSING", "DOWNLOADING", "TRANSCRIBING", "SUMMARIZING", "SAVING"}

BASE = {
    "platform": "bilibili",
    "quality": "fast",
    "model_name": "qwen3-vl-flash",
    "provider_id": "qwen",
    "style": "detailed",
    "format": ["toc", "link", "summary"],
    "screenshot": False,
    "link": False,
    "video_understanding": True,
    "video_interval": 30,
    "grid_size": [4, 4],
}


def bv_id(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def read_lines(path: Path) -> set:
    if not path.exists():
        return set()
    return {ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()}


def done_from_db() -> set:
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute("SELECT DISTINCT video_id FROM video_tasks")
        out = {r[0] for r in cur.fetchall()}
        con.close()
        return out
    except Exception as e:
        print(f"[warn] db read failed: {e}", file=sys.stderr)
        return set()


def count_active() -> int:
    n = 0
    if NOTE_DIR.exists():
        for f in NOTE_DIR.glob("*.status.json"):
            if f.name.endswith("_markdown.status.json"):
                continue  # per-chunk checkpoint status, not a task status
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                if d.get("status") in ACTIVE_STATUSES:
                    n += 1
            except Exception:
                pass
    return n


def wait_for_drain(timeout_s: int = 3600) -> None:
    print("[drain] waiting for already-queued tasks to finish...", file=sys.stderr, flush=True)
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        n = count_active()
        if n == 0:
            print("[drain] queue empty, proceeding", file=sys.stderr, flush=True)
            return
        print(f"[drain] {n} tasks still active, waiting 30s...", file=sys.stderr, flush=True)
        time.sleep(30)
    print("[drain] WARNING: timed out, proceeding anyway", file=sys.stderr, flush=True)


def post(url: str, attempt: int = 0) -> str | None:
    payload = dict(BASE, video_url=url)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if body.get("code") == 0:
            return body["data"].get("task_id")
        print(f"[submit] rejected: {body.get('msg', body)}", file=sys.stderr, flush=True)
        return None
    except Exception as e:
        if attempt < 3:
            time.sleep(5 * (attempt + 1))
            return post(url, attempt + 1)
        print(f"[submit] error: {e}", file=sys.stderr, flush=True)
        return None


def task_status(task_id: str) -> str | None:
    p = NOTE_DIR / f"{task_id}.status.json"
    if not p.exists():
        return "PENDING"
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("status")
    except Exception:
        return None


def _parse_limit() -> int:
    for i, a in enumerate(sys.argv):
        if a == "--limit" and i + 1 < len(sys.argv):
            try:
                return int(sys.argv[i + 1])
            except ValueError:
                return 0
    return 0


def main() -> int:
    urls = [u.strip() for u in INPUT.read_text(encoding="utf-8").splitlines() if u.strip()]
    wait_for_drain()

    done_db = done_from_db()
    done_local = read_lines(DONE)
    failed_local = read_lines(FAILED)
    skip_ids = done_db | {bv_id(u) for u in done_local}
    # do NOT skip previously-failed URLs: retry them
    todo = [u for u in urls if bv_id(u) not in skip_ids]

    limit = _parse_limit()
    if limit and limit > 0:
        todo = todo[:limit]

    print(f"[plan] total={len(urls)} done_db={len(done_db)} done_local={len(done_local)} todo={len(todo)} limit={limit or 'none'}",
          file=sys.stderr, flush=True)

    ok = err = 0
    for i, url in enumerate(todo, 1):
        bid = bv_id(url)
        tid = post(url)
        if not tid:
            err += 1
            with FAILED.open("a", encoding="utf-8") as f:
                f.write(url + "\n")
            print(f"[{i}/{len(todo)}] SUBMIT-FAIL {bid}", file=sys.stderr, flush=True)
            continue

        # wait for terminal state
        while True:
            s = task_status(tid)
            if s in ("SUCCESS", "FAILED"):
                break
            time.sleep(10)

        if s == "SUCCESS":
            ok += 1
            with DONE.open("a", encoding="utf-8") as f:
                f.write(url + "\n")
        else:
            err += 1
            with FAILED.open("a", encoding="utf-8") as f:
                f.write(url + "\n")
        print(f"[{i}/{len(todo)}] {s} {bid} (ok={ok} err={err})", file=sys.stderr, flush=True)

    print(f"[done] ok={ok} err={err}", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
