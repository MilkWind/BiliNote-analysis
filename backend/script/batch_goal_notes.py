#!/usr/bin/env python3
"""Batch-generate BiliNote notes for every video in the goal_videos/*.txt files
listed in goal_videos/temp.txt, honouring each file's per-source requirements.

Per-source requirements come from temp.txt's third column:
  - 详细风格 / 教程风格      -> style = detailed / tutorial
  - 视频理解                -> video_understanding = True (vision model + full download)
  - 文稿转写                -> append the transcript (full_text) to the note end

Why a dedicated driver (instead of the skill's curl loop or batch_submit.py):
  * batch_submit.py / batch_bv_p.py hardcode ONE input file and ONE settings set;
    here every source file needs a different style / video-understanding flag and
    a per-file "append transcript" toggle.
  * The backend schedules each task onto a 3-worker pool and each task BLOCKS a
    worker for its whole runtime (~90s), so we keep a small in-flight window and
    wait for terminal states instead of firing 1508 submissions.

Resume / dedup:
  * Skips any BV already present in bili_note.db (video_tasks) -> survives restarts.
  * Skips URLs recorded as SUCCESS in the progress JSONL.
  * Failed videos are retried up to --max-attempts.

Usage (run from backend/):
    python script/batch_goal_notes.py --verify        # one video, then stop
    python script/batch_goal_notes.py                 # full run
    python script/batch_goal_notes.py --only "周展"    # single source file
    python script/batch_goal_notes.py --limit 20
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.request
from collections import deque
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
GOAL = ROOT / "goal_videos"
NOTE_DIR = BACKEND / "note_results"
DB = BACKEND / "bili_note.db"
API = "http://localhost:8483/api/generate_note"
PROGRESS = GOAL / "_goal_notes_progress.jsonl"
LOG = GOAL / "_goal_notes_run.log"

ACTIVE_STATUSES = {"PENDING", "PARSING", "DOWNLOADING", "TRANSCRIBING",
                   "SUMMARIZING", "FORMATTING", "SAVING", "RUNNING"}

TEXT_MODEL = "qwen3.7-plus"
VISION_MODEL = "qwen3-vl-plus"

# file label -> requirements (from goal_videos/temp.txt)
MANIFEST = [
    {"file": "KAPI卡皮品牌研究社", "style": "detailed", "vu": False, "append_transcript": True},
    {"file": "地球有点莽", "style": "detailed", "vu": False, "append_transcript": True},
    {"file": "为什么叫QQ 硬核拆解系列合集", "style": "detailed", "vu": False, "append_transcript": True},
    {"file": "周展", "style": "detailed", "vu": True, "append_transcript": False},
    {"file": "汤明月说", "style": "detailed", "vu": False, "append_transcript": True},
    {"file": "大闫叨叨", "style": "detailed", "vu": False, "append_transcript": False},
    {"file": "前端小卒 web碎碎念合集", "style": "tutorial", "vu": False, "append_transcript": False},
    {"file": "程序员小Dan 软件架构师合集", "style": "detailed", "vu": False, "append_transcript": True},
    {"file": "程序员小Dan 计算机专业面试总结合集", "style": "detailed", "vu": False, "append_transcript": True},
]

TRANSCRIPT_HEADER = "## 文稿转写"


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, file=sys.stderr, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def bv_of(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1].split("?")[0]


def done_from_db() -> set[str]:
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute("SELECT DISTINCT video_id FROM video_tasks")
        out = {r[0] for r in cur.fetchall()}
        con.close()
        return out
    except Exception as e:  # pragma: no cover
        log(f"[warn] db read failed: {e}")
        return set()


def progress_success() -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not PROGRESS.exists():
        return out
    for ln in PROGRESS.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rec = json.loads(ln)
        except Exception:
            continue
        if rec.get("status") == "SUCCESS":
            out[rec["bv"]] = rec
    return out


def record(rec: dict) -> None:
    rec = dict(rec)
    rec["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with PROGRESS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def build_manifest() -> list[dict]:
    items: list[dict] = []
    for entry in MANIFEST:
        path = GOAL / f"{entry['file']}.txt"
        if not path.exists():
            log(f"[warn] missing list file: {path}")
            continue
        for ln in path.read_text(encoding="utf-8").splitlines():
            url = ln.strip()
            if not url:
                continue
            items.append({
                "file": entry["file"],
                "url": url,
                "bv": bv_of(url),
                "style": entry["style"],
                "vu": entry["vu"],
                "append_transcript": entry["append_transcript"],
            })
    return items


def count_active() -> int:
    n = 0
    if NOTE_DIR.exists():
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
        n = count_active()
        if n == 0:
            return
        log(f"[drain] {n} tasks still active, waiting 30s...")
        time.sleep(30)
    log("[drain] WARNING: timed out, proceeding anyway")


def payload(item: dict) -> dict:
    return {
        "video_url": item["url"],
        "platform": "bilibili",
        "quality": "fast",
        "provider_id": "qwen",
        "model_name": VISION_MODEL if item["vu"] else TEXT_MODEL,
        "style": item["style"],
        "format": ["toc", "link", "summary"],
        "screenshot": False,
        "link": False,
        "video_understanding": item["vu"],
        "video_interval": 30 if item["vu"] else 0,
        "grid_size": [4, 4] if item["vu"] else [],
    }


def post(item: dict, attempt: int = 0) -> str | None:
    data = json.dumps(payload(item)).encode("utf-8")
    req = urllib.request.Request(API, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if body.get("code") == 0:
            return body["data"].get("task_id")
        log(f"[submit] rejected {item['bv']}: {body.get('msg', body)}")
        return None
    except Exception as e:
        if attempt < 3:
            time.sleep(5 * (attempt + 1))
            return post(item, attempt + 1)
        log(f"[submit] error {item['bv']}: {e}")
        return None


def task_status(task_id: str) -> str:
    p = NOTE_DIR / f"{task_id}.status.json"
    if not p.exists():
        return "PENDING"
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("status", "PENDING")
    except Exception:
        return "PENDING"


def append_transcript(task_id: str, bv: str) -> bool:
    """Idempotently append the transcript full_text to the note markdown end."""
    md = NOTE_DIR / f"{task_id}_markdown.md"
    ts = NOTE_DIR / f"{task_id}_transcript.json"
    if not md.exists() or not ts.exists():
        log(f"[transcript] skip {bv}: markdown or transcript missing")
        return False
    text = md.read_text(encoding="utf-8")
    if TRANSCRIPT_HEADER in text:
        return True
    try:
        full = (json.loads(ts.read_text(encoding="utf-8")).get("full_text") or "").strip()
    except Exception as e:
        log(f"[transcript] read failed {bv}: {e}")
        return False
    if not full:
        log(f"[transcript] empty transcript for {bv}")
        return False
    md.write_text(text.rstrip() + f"\n\n---\n\n{TRANSCRIPT_HEADER}\n\n{full}\n", encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="BiliNote batch driver for goal_videos sources")
    ap.add_argument("--verify", action="store_true", help="process a single video and exit")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="", help="only sources whose label contains this substring")
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--max-attempts", type=int, default=3)
    ap.add_argument("--poll", type=float, default=10.0)
    ap.add_argument("--stall", type=float, default=2400.0, help="seconds before an active task is treated as orphaned")
    ap.add_argument("--budget-seconds", type=float, default=0.0,
                    help="stop submitting new tasks after N seconds (drain in-flight, then exit). 0 = unlimited")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    items = build_manifest()
    if args.only:
        items = [it for it in items if args.only in it["file"]]
    done_db = done_from_db()
    done_prog = progress_success()
    todo = [it for it in items if it["bv"] not in done_db and it["bv"] not in done_prog]
    if args.limit:
        todo = todo[: args.limit]
    if args.verify:
        todo = todo[:1]

    log(f"[plan] sources={len(MANIFEST)} total={len(items)} done_db={len(done_db)} "
        f"done_progress={len(done_prog)} todo={len(todo)} concurrency={args.concurrency}")

    if args.dry_run:
        for it in todo[:20]:
            print(json.dumps({**it, "payload": payload(it)}, ensure_ascii=False))
        log(f"[dry-run] {len(todo)} tasks would be submitted")
        return 0
    if not todo:
        log("[done] nothing to do")
        return 0

    wait_for_drain()

    pending = deque(todo)
    attempts: dict[str, int] = {}
    active: dict[str, dict] = {}       # task_id -> item
    changed: dict[str, float] = {}     # task_id -> last state-change time
    last_state: dict[str, str] = {}
    ok = err = done_n = 0
    total = len(todo)
    deadline = time.time() + args.budget_seconds if args.budget_seconds else None
    draining = False

    def fill() -> None:
        if draining:
            return
        while pending and len(active) < args.concurrency:
            it = pending.popleft()
            tid = post(it)
            if not tid:
                attempts[it["bv"]] = attempts.get(it["bv"], 0) + 1
                if attempts[it["bv"]] < args.max_attempts:
                    pending.append(it)
                else:
                    record({**it, "status": "FAILED", "error": "submit-failed"})
                    nonlocal err
                    err += 1
                    log(f"[{done_n + err}/{total}] SUBMIT-FAIL {it['bv']} ({it['file']})")
                time.sleep(5)
                continue
            active[tid] = it
            changed[tid] = time.time()
            last_state[tid] = "PENDING"

    while pending or active:
        if deadline and not draining and time.time() >= deadline:
            draining = True
            pending.clear()
            log(f"[budget] {int(args.budget_seconds)}s reached; draining {len(active)} in-flight, "
                f"remaining will resume on the next run")
        fill()
        for tid in list(active):
            s = task_status(tid)
            if s != last_state.get(tid):
                last_state[tid] = s
                changed[tid] = time.time()
            if s == "SUCCESS":
                it = active.pop(tid)
                if it["append_transcript"]:
                    append_transcript(tid, it["bv"])
                record({**it, "status": "SUCCESS", "task_id": tid})
                ok += 1
                done_n += 1
                log(f"[{done_n + err}/{total}] SUCCESS {it['bv']} ({it['file']}) ok={ok} err={err}")
            elif s == "FAILED" or time.time() - changed[tid] > args.stall:
                it = active.pop(tid)
                attempts[it["bv"]] = attempts.get(it["bv"], 0) + 1
                if s == "FAILED" and attempts[it["bv"]] < args.max_attempts:
                    pending.append(it)
                    log(f"[{done_n + err}/{total}] retry {attempts[it['bv']]}/{args.max_attempts} {it['bv']}")
                else:
                    record({**it, "status": "FAILED", "task_id": tid, "error": s})
                    err += 1
                    log(f"[{done_n + err}/{total}] FAILED {it['bv']} ({it['file']}) state={s} ok={ok} err={err}")
        if pending or active:
            time.sleep(args.poll)

    log(f"[done] ok={ok} err={err} total={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
