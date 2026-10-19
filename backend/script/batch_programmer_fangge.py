#!/usr/bin/env python3
"""Batch-generate notes for 程序员方格's 2026 分P, category by category.

Input:  goal_videos/程序员方格_分P分类.json (produced by
        script/pagination_query/classify_programmer_fangge.py)

Settings (voice/audio parsing + text transcription):
  - style = detailed
  - format = toc + link + summary
  - video_understanding = false  (no frame extraction; audio/subtitles only)
  - transcript appended to each note under "## 文稿转写"

Notes are written to:
  goal_videos/程序员方格_笔记/<category>/<NNN> <title>.md

Resume / safety:
  * progress is appended to goal_videos/_programmer_fangge_progress.jsonl;
    SUCCESS entries are skipped on the next run, FAILED entries are retried.
  * at most one in-flight task per BV (concurrent pages of the same video
    trigger Bilibili HTTP 412).
  * the backend has 3 workers; keep --concurrency <= 3.

Usage (run from backend/):
    python script/batch_programmer_fangge.py --verify
    python script/batch_programmer_fangge.py
    python script/batch_programmer_fangge.py --category 03-React --limit 5
    python script/batch_programmer_fangge.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from collections import deque
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
GOAL = ROOT / "goal_videos"
CLASS_JSON = GOAL / "程序员方格_分P分类.json"
NOTE_DIR = BACKEND / "note_results"
OUT_DIR = GOAL / "程序员方格_笔记"
PROGRESS = GOAL / "_programmer_fangge_progress.jsonl"
LOG = GOAL / "_programmer_fangge_run.log"
API = "http://localhost:8483/api/generate_note"

ACTIVE_STATUSES = {
    "PENDING", "RUNNING", "PARSING", "DOWNLOADING", "TRANSCRIBING",
    "SUMMARIZING", "FORMATTING", "SAVING",
}

PAYLOAD = {
    "platform": "bilibili",
    "quality": "fast",
    "provider_id": "qwen",
    "model_name": "qwen3.7-plus",
    "style": "detailed",
    "format": ["toc", "link", "summary"],
    "screenshot": False,
    "link": False,
    "video_understanding": False,
    "video_interval": 0,
    "grid_size": [],
}

TRANSCRIPT_HEADER = "## 文稿转写"

_INVALID = {
    "/": "／", "\\": "＼", ":": "：", "*": "＊", "?": "？",
    '"': "＂", "<": "＜", ">": "＞", "|": "｜",
}


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, file=sys.stderr, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def sanitize(title: str, limit: int = 100) -> str:
    t = "".join(_INVALID.get(c, c) for c in title)
    t = "".join(c for c in t if c >= " " or c == "\t")
    t = re.sub(r"\s+", " ", t).strip().rstrip(". ")
    if len(t) > limit:
        t = t[:limit].rstrip(". ")
    return t or "untitled"


def load_items() -> list[dict]:
    data = json.loads(CLASS_JSON.read_text(encoding="utf-8"))
    items: list[dict] = []
    for cat in data["categories"]:
        for idx, it in enumerate(cat["items"], 1):
            items.append({
                **it,
                "category": cat["slug"],
                "category_label": cat["label"],
                "seq": idx,
            })
    return items


def done_urls() -> set[str]:
    done: set[str] = set()
    if not PROGRESS.exists():
        return done
    for line in PROGRESS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        if rec.get("status") == "SUCCESS":
            done.add(rec["url"])
    return done


def record(rec: dict) -> None:
    rec = dict(rec)
    rec["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with PROGRESS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def task_status(task_id: str) -> str:
    p = NOTE_DIR / f"{task_id}.status.json"
    if not p.exists():
        return "PENDING"
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("status", "PENDING")
    except Exception:
        return "PENDING"


def active_count() -> int:
    n = 0
    if not NOTE_DIR.exists():
        return n
    for f in NOTE_DIR.glob("*.status.json"):
        if f.name.endswith("_markdown.status.json"):
            continue
        try:
            if json.loads(f.read_text(encoding="utf-8")).get("status") in ACTIVE_STATUSES:
                n += 1
        except Exception:
            pass
    return n


def wait_for_drain(timeout_s: int = 3600) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        n = active_count()
        if n == 0:
            return
        log(f"[drain] {n} tasks still active, waiting 30s...")
        time.sleep(30)
    log("[drain] WARNING: timed out, proceeding anyway")


def post(item: dict, attempt: int = 0) -> str | None:
    payload = dict(PAYLOAD, video_url=item["url"])
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if body.get("code") == 0:
            return body["data"].get("task_id")
        log(f"[submit] rejected {item['bvid']} P{item['page']}: {body.get('msg', body)}")
        return None
    except Exception as e:  # noqa: BLE001
        if attempt < 3:
            time.sleep(5 * (attempt + 1))
            return post(item, attempt + 1)
        log(f"[submit] error {item['bvid']} P{item['page']}: {e}")
        return None


def append_transcript(task_id: str) -> bool:
    md = NOTE_DIR / f"{task_id}_markdown.md"
    ts = NOTE_DIR / f"{task_id}_transcript.json"
    if not md.exists():
        return False
    text = md.read_text(encoding="utf-8")
    if TRANSCRIPT_HEADER in text:
        return True
    if not ts.exists():
        log(f"[transcript] missing {ts.name}")
        return False
    try:
        full = (json.loads(ts.read_text(encoding="utf-8")).get("full_text") or "").strip()
    except Exception as e:  # noqa: BLE001
        log(f"[transcript] read failed {ts.name}: {e}")
        return False
    if not full:
        log(f"[transcript] empty {ts.name}")
        return False
    md.write_text(text.rstrip() + f"\n\n---\n\n{TRANSCRIPT_HEADER}\n\n{full}\n", encoding="utf-8")
    return True


def copy_note(task_id: str, item: dict) -> Path | None:
    md = NOTE_DIR / f"{task_id}_markdown.md"
    if not md.exists():
        log(f"[save] missing markdown for {task_id}")
        return None
    append_transcript(task_id)
    dest_dir = OUT_DIR / item["category"]
    dest_dir.mkdir(parents=True, exist_ok=True)
    base = f"{item['seq']:03d} {sanitize(item['title'])}"
    dest = dest_dir / f"{base}.md"
    n = 2
    while dest.exists():
        dest = dest_dir / f"{base} ({n}).md"
        n += 1
    dest.write_text(md.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def main() -> int:
    ap = argparse.ArgumentParser(description="Batch notes for 程序员方格 2026 分P")
    ap.add_argument("--verify", action="store_true", help="process one item and exit")
    ap.add_argument("--category", default="", help="only categories whose slug contains this")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--max-attempts", type=int, default=3)
    ap.add_argument("--poll", type=float, default=10.0)
    ap.add_argument("--stall", type=float, default=2400.0,
                    help="seconds before an unchanging task is treated as orphaned")
    ap.add_argument("--budget-seconds", type=float, default=0.0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    items = load_items()
    if args.category:
        items = [it for it in items if args.category in it["category"]]
    done = done_urls()
    todo = [it for it in items if it["url"] not in done]
    if args.limit:
        todo = todo[: args.limit]
    if args.verify:
        todo = todo[:1]

    log(f"[plan] total={len(items)} done={len(done)} todo={len(todo)} "
        f"concurrency={args.concurrency} category={args.category or 'all'}")

    if args.dry_run:
        for it in todo[:20]:
            print(json.dumps({**it, "payload": dict(PAYLOAD, video_url=it["url"])},
                             ensure_ascii=False))
        log(f"[dry-run] {len(todo)} tasks would be submitted")
        return 0
    if not todo:
        log("[done] nothing to do")
        return 0

    wait_for_drain()

    pending = deque(todo)
    attempts: dict[str, int] = {}
    active: dict[str, dict] = {}            # task_id -> item
    active_bvs: set[str] = set()
    changed: dict[str, float] = {}
    last_state: dict[str, str] = {}
    ok = err = 0
    total = len(todo)
    deadline = time.time() + args.budget_seconds if args.budget_seconds else None
    draining = False

    def fill() -> None:
        nonlocal err
        if draining:
            return
        while pending and len(active) < args.concurrency:
            # pick the first pending item whose BV is not already downloading
            idx = next((i for i, it in enumerate(pending) if it["bvid"] not in active_bvs), None)
            if idx is None:
                return
            it = pending[idx]
            del pending[idx]
            tid = post(it)
            if not tid:
                attempts[it["url"]] = attempts.get(it["url"], 0) + 1
                if attempts[it["url"]] < args.max_attempts:
                    pending.append(it)
                else:
                    record({**it, "status": "FAILED", "error": "submit-failed"})
                    err += 1
                    log(f"[{ok + err}/{total}] SUBMIT-FAIL {it['bvid']} P{it['page']}")
                time.sleep(3)
                continue
            active[tid] = it
            active_bvs.add(it["bvid"])
            changed[tid] = time.time()
            last_state[tid] = "PENDING"

    while pending or active:
        if deadline and not draining and time.time() >= deadline:
            draining = True
            pending.clear()
            log(f"[budget] reached; draining {len(active)} in-flight tasks")
        fill()
        for tid in list(active):
            it = active[tid]
            s = task_status(tid)
            if s != last_state.get(tid):
                last_state[tid] = s
                changed[tid] = time.time()
            if s == "SUCCESS":
                active.pop(tid)
                active_bvs.discard(it["bvid"])
                dest = copy_note(tid, it)
                record({**it, "status": "SUCCESS", "task_id": tid,
                        "note_path": str(dest.relative_to(ROOT)).replace("\\", "/") if dest else None})
                ok += 1
                log(f"[{ok + err}/{total}] SUCCESS {it['bvid']} P{it['page']} "
                    f"{it['category']} ok={ok} err={err}")
            elif s == "FAILED" or time.time() - changed[tid] > args.stall:
                active.pop(tid)
                active_bvs.discard(it["bvid"])
                attempts[it["url"]] = attempts.get(it["url"], 0) + 1
                if s == "FAILED" and attempts[it["url"]] < args.max_attempts:
                    pending.append(it)
                    log(f"[retry {attempts[it['url']]}/{args.max_attempts}] "
                        f"{it['bvid']} P{it['page']}")
                else:
                    record({**it, "status": "FAILED", "task_id": tid, "error": s})
                    err += 1
                    log(f"[{ok + err}/{total}] FAILED {it['bvid']} P{it['page']} "
                        f"state={s} ok={ok} err={err}")
        if pending or active:
            time.sleep(args.poll)

    log(f"[done] ok={ok} err={err} total={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
