#!/usr/bin/env python3
"""Sequentially generate notes for every P of a multi-part Bilibili video.

Reads URLs from urls.txt (one per line, e.g. .../BVxxx/?p=N), submits each to
the backend /generate_note ONE at a time, and waits for a terminal state before
the next — the backend threadpool blocks a thread per queued task for its whole
runtime and concurrent same-video downloads trigger HTTP 412, so bursts are
dangerous.

Dedup / resume:
- Skips URLs already recorded in urls_done.txt (previous runs).
- Skips URLs in urls_failed.txt.
- Note: DB dedup is useless here because every P shares the same BV video_id.
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

API = "http://localhost:8483/api/generate_note"
INPUT = Path("urls.txt")
DONE = Path("urls_done.txt")
FAILED = Path("urls_failed.txt")
NOTE_DIR = Path("note_results")

ACTIVE_STATUSES = {"PENDING", "RUNNING", "PARSING", "DOWNLOADING", "TRANSCRIBING", "SUMMARIZING", "SAVING"}

MAX_ATTEMPTS = 3

BASE = {
    "platform": "bilibili",
    "quality": "fast",
    "model_name": "qwen3.7-plus",
    "provider_id": "qwen",
    "style": "tutorial",
    "format": ["toc", "link", "summary"],
    "screenshot": False,
    "link": False,
    "video_understanding": True,
    "video_interval": 3,
    "grid_size": [4, 4],
}


def read_lines(path: Path) -> set:
    if not path.exists():
        return set()
    return {ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()}


def count_active() -> int:
    n = 0
    if NOTE_DIR.exists():
        for f in NOTE_DIR.glob("*.status.json"):
            if f.name.endswith("_markdown.status.json"):
                continue
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                if d.get("status") in ACTIVE_STATUSES:
                    n += 1
            except Exception:
                pass
    return n


def wait_for_drain(timeout_s: int = 3600) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if count_active() == 0:
            return
        print(f"[drain] {count_active()} tasks still active, waiting 30s...", file=sys.stderr, flush=True)
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


def wait_terminal(task_id: str, stall_timeout: float = 720.0) -> str:
    """Poll until SUCCESS/FAILED, or mark FAILED if the status file stops
    changing (e.g. the task was orphaned by a backend restart)."""
    last_state = None
    last_change = time.time()
    while True:
        s = task_status(task_id)
        if s in ("SUCCESS", "FAILED"):
            return s
        if s != last_state:
            last_state = s
            last_change = time.time()
        elif time.time() - last_change > stall_timeout:
            print(f"[stall] task {task_id} stuck at '{s}' for {int(stall_timeout)}s, aborting", file=sys.stderr, flush=True)
            return "FAILED"
        time.sleep(10)


def main() -> int:
    urls = [u.strip() for u in INPUT.read_text(encoding="utf-8").splitlines() if u.strip()]
    wait_for_drain()

    done = read_lines(DONE)
    failed = read_lines(FAILED)
    todo = [u for u in urls if u not in done]
    # previously-failed URLs are retried (not skipped), per batch_submit.py

    print(f"[plan] total={len(urls)} done={len(done)} failed={len(failed)} todo={len(todo)}",
          file=sys.stderr, flush=True)

    ok = err = 0
    for i, url in enumerate(todo, 1):
        s = "FAILED"
        for attempt in range(1, MAX_ATTEMPTS + 1):
            tid = post(url)
            if not tid:
                break
            s = wait_terminal(tid)
            if s == "SUCCESS":
                break
            print(f"[{i}/{len(todo)}] attempt {attempt}/{MAX_ATTEMPTS} {s} {url}",
                  file=sys.stderr, flush=True)
            time.sleep(15 * attempt)

        if s == "SUCCESS":
            ok += 1
            with DONE.open("a", encoding="utf-8") as f:
                f.write(url + "\n")
        else:
            err += 1
            with FAILED.open("a", encoding="utf-8") as f:
                f.write(url + "\n")
        print(f"[{i}/{len(todo)}] {s} {url} (ok={ok} err={err})", file=sys.stderr, flush=True)

    print(f"[done] ok={ok} err={err}", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
