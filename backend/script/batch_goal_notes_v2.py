#!/usr/bin/env python3
"""Batch-generate notes for the sources listed in goal_videos/temp.txt (v2).

This is the successor to ``batch_goal_notes.py`` for the 2026-10 source set.
It reads one URL per line from ``goal_videos/<source>.txt`` (built by
``pagination_query/build_goal_video_lists.py``) and submits each item to the
running backend, honouring the per-source requirements from temp.txt:

  - 详细风格 / 教程风格      -> style = detailed / tutorial
  - 图像理解 / 图片理解      -> video_understanding = True (vision model + full download)
  - 文稿转写                 -> append the transcript (full_text) to the note end

Provider defaults to Volcengine Ark, model ``doubao-seed-2-1-lite-260915``
(a vision-language model, so it covers both text and frame tasks). Override with
``--provider`` / ``--text-model`` / ``--vision-model``.

Prerequisites
-------------
* Backend running. Default target is ``http://localhost:8483``; a second backend
  on another port (e.g. the 32-worker instance used by ``run_full_plan.py``) is
  selected with ``--api-base http://localhost:8484``.
* The provider's API key stored in ``bili_note.db``. A ``--check`` preflight
  makes one minimal chat call and refuses to submit if the model is not
  activated, instead of discovering that 7,000 tasks later.
* Media for the URLs (optional but strongly recommended): see
  ``predownload_goal_media.py``. Without it each task downloads during generation.

Resume / dedupe:
  * Builds a ``video_id`` (``BV...`` or ``BV..._pN``) for every URL.
  * Skips ids already recorded in ``video_tasks`` (previous submissions),
    except ids that this driver itself recorded as FAILED (retried).
  * Skips URLs recorded as SUCCESS in the v2 progress JSONL.
  * Skips BVs listed in ``_goal_notes_skip.txt``.
  * Retries failures up to ``--max-attempts``.

Usage (run from backend/):
    python script/batch_goal_notes_v2.py --dry-run          # show the plan
    python script/batch_goal_notes_v2.py --check            # provider preflight only
    python script/batch_goal_notes_v2.py --verify           # one task, wait, exit
    python script/batch_goal_notes_v2.py                    # full run
    python script/batch_goal_notes_v2.py --only 渡一         # one source
    python script/batch_goal_notes_v2.py --api-base http://localhost:8484 --concurrency 32

Adding or changing sources
--------------------------
Edit the ``SOURCES`` table (label, style, video-understanding, append-transcript)
so it matches ``goal_videos/temp.txt``; each label needs a matching
``goal_videos/<label>.txt`` URL list.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
import time
import urllib.request
from collections import deque
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
GOAL = ROOT / "goal_videos"
DB = BACKEND / "bili_note.db"
API = "http://localhost:8483/api/generate_note"
PROGRESS = GOAL / "_goal_notes_progress_v2.jsonl"
SKIP = GOAL / "_goal_notes_skip.txt"
LOG = GOAL / "_goal_notes_run_v2.log"

ACTIVE_STATUSES = {"PENDING", "PARSING", "DOWNLOADING", "TRANSCRIBING",
                   "SUMMARIZING", "FORMATTING", "SAVING", "RUNNING"}

TRANSCRIPT_HEADER = "## 文稿转写"

# source label -> (style, video_understanding, append_transcript)
SOURCES: list[tuple[str, str, bool, bool]] = [
    ("bytezhou", "detailed", False, False),
    ("dadafastrun", "detailed", False, False),
    ("deepseekharness_", "tutorial", True, False),
    ("渡一 前端提薪课精选合集", "tutorial", True, False),
    ("小张阿姨的AI教学", "detailed", True, True),
    ("泽希讲求职", "detailed", False, True),
    ("ezindie小产品变现", "detailed", False, True),
    ("炟烨 城市观察合集", "detailed", False, True),
    ("瓜子项目社", "detailed", True, True),
    ("温少创业记", "detailed", False, True),
    ("喵类思维", "detailed", False, True),
    ("思维实验室", "detailed", False, True),
    ("你要相信光的呀哦", "detailed", False, True),
    ("小鱼爱配音x", "detailed", False, True),
    ("AI深海圈", "detailed", False, True),
    ("我捞捞捞", "detailed", False, True),
    ("程序员Web3社区", "detailed", False, True),
    ("大雨说Java", "tutorial", False, False),
    ("与书籍度过漫长岁月", "detailed", False, True),
    ("老猫乔諵 我在B站做UP合集", "detailed", False, True),
    ("前端小码哥", "tutorial", True, False),
    ("高江子", "detailed", True, True),
    ("熠辉IndieDev", "detailed", True, True),
    ("PlanJ_", "detailed", False, True),
    ("程序员方格", "detailed", True, False),
]

# 笔记待生成合集: (BV, style, video_understanding, append_transcript)
PENDING: list[tuple[str, str, bool, bool]] = [
    ("BV1vK9eBREyD", "detailed", False, True),
    ("BV1Hhpu6pEa1", "detailed", False, True),
    ("BV19rpE6iEpN", "detailed", True, True),
    ("BV1Zka56QEsv", "detailed", False, True),
    ("BV154426xEha", "detailed", True, True),
    ("BV1Tit86MECG", "detailed", False, True),
]
PENDING_LABEL = "笔记待生成合集"


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, file=sys.stderr, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def video_id_of(url: str) -> str:
    m = re.search(r"(BV[0-9A-Za-z]{10})", url)
    if not m:
        return ""
    bv = m.group(1)
    pm = re.search(r"[?&]p=(\d+)", url)
    return f"{bv}_p{pm.group(1)}" if pm else bv


def bv_of(url: str) -> str:
    m = re.search(r"(BV[0-9A-Za-z]{10})", url)
    return m.group(1) if m else ""


def note_dirs() -> list[Path]:
    return [BACKEND / "note_results", ROOT / "note_results"]


def status_path(task_id: str) -> Path | None:
    for d in note_dirs():
        p = d / f"{task_id}.status.json"
        if p.exists():
            return p
    return None


def task_status(task_id: str) -> str:
    p = status_path(task_id)
    if not p:
        return "PENDING"
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("status", "PENDING")
    except Exception:
        return "PENDING"


def count_active() -> int:
    n = 0
    for d in note_dirs():
        if not d.exists():
            continue
        for f in d.glob("*.status.json"):
            if f.name.endswith("_markdown.status.json"):
                continue
            try:
                if json.loads(f.read_text(encoding="utf-8")).get("status") in ACTIVE_STATUSES:
                    n += 1
            except Exception:
                pass
    return n


def wait_for_drain(timeout_s: int = 7200) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        n = count_active()
        if n == 0:
            return
        log(f"[drain] {n} tasks still active, waiting 30s...")
        time.sleep(30)
    log("[drain] WARNING: timed out, proceeding anyway")


def progress_records() -> list[dict]:
    out: list[dict] = []
    if not PROGRESS.exists():
        return out
    for ln in PROGRESS.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out


def record(rec: dict) -> None:
    rec = dict(rec)
    rec["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with PROGRESS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def progress_success_ids() -> set[str]:
    return {r.get("video_id") or video_id_of(r.get("url", ""))
            for r in progress_records() if r.get("status") == "SUCCESS"}


def progress_failed_ids() -> set[str]:
    return {r.get("video_id") or video_id_of(r.get("url", ""))
            for r in progress_records() if r.get("status") == "FAILED"}


def db_video_ids() -> set[str]:
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute("SELECT DISTINCT video_id FROM video_tasks")
        out = {r[0] for r in cur.fetchall()}
        con.close()
        return out
    except Exception as e:
        log(f"[warn] db read failed: {e}")
        return set()


def skip_bvs() -> set[str]:
    if not SKIP.exists():
        return set()
    return {
        ln.strip()
        for ln in SKIP.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.lstrip().startswith("#")
    }


def provider_row(provider_id: str) -> dict | None:
    try:
        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        row = con.execute("SELECT * FROM providers WHERE id = ?", (provider_id,)).fetchone()
        con.close()
        return dict(row) if row else None
    except Exception as e:
        log(f"[warn] provider read failed: {e}")
        return None


def preflight(provider_id: str, models: list[str]) -> bool:
    """Verify the provider key + model are actually callable before submitting."""
    row = provider_row(provider_id)
    if not row:
        log(f"[preflight] provider '{provider_id}' not found in DB")
        return False
    if not row.get("api_key"):
        log(f"[preflight] provider '{provider_id}' has no API key in DB")
        return False
    try:
        from openai import OpenAI
    except ImportError:
        log("[preflight] openai package missing; skipping model call")
        return True
    client = OpenAI(api_key=row["api_key"], base_url=row["base_url"],
                    timeout=30, max_retries=0)
    ok = True
    for model in dict.fromkeys(models):
        last = ""
        for attempt in range(1, 6):
            try:
                client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "只回复：OK"}],
                    max_tokens=5,
                )
                log(f"[preflight] {provider_id}/{model} OK")
                last = ""
                break
            except Exception as e:
                last = str(e)
                if attempt < 5:
                    log(f"[preflight] {provider_id}/{model} attempt {attempt} failed; "
                        f"waiting 15s (activation may still be propagating)")
                    time.sleep(15)
        if last:
            if "ModelNotOpen" in last:
                log(f"[preflight] {provider_id}/{model} 未开通：请在火山方舟控制台"
                    f"（console.volcengine.com/ark → 开通管理）激活该模型，或改用已开通的模型/推理接入点")
            else:
                log(f"[preflight] {provider_id}/{model} 失败：{last[:300]}")
            ok = False
    return ok


def build_items() -> list[dict]:
    items: list[dict] = []
    # Pending BVs are small in number and explicitly requested; do them first.
    for bv, style, vu, append in PENDING:
        items.append({"source": PENDING_LABEL,
                      "url": f"https://www.bilibili.com/video/{bv}",
                      "style": style, "vu": vu, "append_transcript": append})
    for label, style, vu, append in SOURCES:
        path = GOAL / f"{label}.txt"
        if not path.exists():
            log(f"[warn] missing list file: {path}")
            continue
        for ln in path.read_text(encoding="utf-8").splitlines():
            url = ln.strip()
            if not url:
                continue
            items.append({"source": label, "url": url, "style": style,
                          "vu": vu, "append_transcript": append})
    for it in items:
        it["video_id"] = video_id_of(it["url"])
        it["bv"] = bv_of(it["url"])
    return items


def payload(item: dict, provider: str, text_model: str, vision_model: str,
            _format: list[str], quality: str) -> dict:
    return {
        "video_url": item["url"],
        "platform": "bilibili",
        "quality": quality,
        "provider_id": provider,
        "model_name": vision_model if item["vu"] else text_model,
        "style": item["style"],
        "format": _format,
        "screenshot": False,
        "link": False,
        "video_understanding": item["vu"],
        "video_interval": 30 if item["vu"] else 0,
        "grid_size": [4, 4] if item["vu"] else [],
    }


def post(item: dict, body: dict, attempt: int = 0) -> str | None:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(API, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            js = json.loads(resp.read().decode("utf-8"))
        if js.get("code") == 0:
            return js["data"].get("task_id")
        log(f"[submit] rejected {item['video_id']}: {js.get('msg', js)}")
        return None
    except Exception as e:
        if attempt < 3:
            time.sleep(5 * (attempt + 1))
            return post(item, body, attempt + 1)
        log(f"[submit] error {item['video_id']}: {e}")
        return None


def note_file(task_id: str, suffix: str) -> Path | None:
    for d in note_dirs():
        p = d / f"{task_id}{suffix}"
        if p.exists():
            return p
    return None


MEDIA_DIRS = [BACKEND / "data" / "data", BACKEND / "download_audios"]


def cleanup_media(video_id: str) -> None:
    """Delete the downloaded video/audio for a finished task.

    Volc SeedASR does not emit the ``transcription_finished`` cleanup signal,
    and full videos for video_understanding are large, so the driver removes
    the media itself after a SUCCESS. Notes/transcripts in note_results are
    left untouched.
    """
    if not video_id:
        return
    removed = 0
    for d in MEDIA_DIRS:
        if not d.exists():
            continue
        for p in d.iterdir():
            if not p.is_file():
                continue
            if p.name.split(".", 1)[0] != video_id:
                continue
            try:
                p.unlink()
                removed += 1
            except Exception as e:  # noqa: BLE001
                log(f"[cleanup] failed {p}: {e}")
    if removed:
        log(f"[cleanup] removed {removed} media file(s) for {video_id}")


def append_transcript(task_id: str, video_id: str) -> bool:
    """Idempotently append the transcript full_text to the note markdown end."""
    md = ts = None
    # SUCCESS is written just before the router saves the markdown, so give the
    # note file a short grace period.
    for _ in range(60):
        md = note_file(task_id, "_markdown.md")
        ts = note_file(task_id, "_transcript.json")
        if md and ts:
            break
        time.sleep(1)
    if not md or not ts:
        log(f"[transcript] skip {video_id}: markdown or transcript missing")
        return False
    text = md.read_text(encoding="utf-8")
    if TRANSCRIPT_HEADER in text:
        return True
    try:
        full = (json.loads(ts.read_text(encoding="utf-8")).get("full_text") or "").strip()
    except Exception as e:
        log(f"[transcript] read failed {video_id}: {e}")
        return False
    if not full:
        log(f"[transcript] empty transcript for {video_id}")
        return False
    md.write_text(text.rstrip() + f"\n\n---\n\n{TRANSCRIPT_HEADER}\n\n{full}\n", encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="BiliNote batch driver v2 (Ark)")
    ap.add_argument("--provider", default="ark")
    ap.add_argument("--api-base", default="http://localhost:8483",
                    help="backend base URL (use 8484 for the 64-worker instance)")
    ap.add_argument("--text-model", default="doubao-seed-2-1-lite-260915")
    ap.add_argument("--vision-model", default="doubao-seed-2-1-lite-260915")
    ap.add_argument("--format", default="toc,link,summary")
    ap.add_argument("--quality", default="fast")
    ap.add_argument("--verify", action="store_true", help="process a single video and exit")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="", help="only sources whose label contains this substring")
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--max-attempts", type=int, default=3)
    ap.add_argument("--poll", type=float, default=15.0)
    ap.add_argument("--stall", type=float, default=3600.0,
                    help="seconds before an active task is treated as orphaned")
    ap.add_argument("--budget-seconds", type=float, default=0.0,
                    help="stop submitting new tasks after N seconds")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true", help="preflight provider/models and exit")
    ap.add_argument("--skip-preflight", action="store_true")
    ap.add_argument("--keep-media", action="store_true",
                    help="keep downloaded mp4/mp3 after each successful task")
    ap.add_argument("--min-free-gb", type=float, default=30.0,
                    help="stop submitting new tasks if the disk has less free space than this")
    args = ap.parse_args()
    global API
    API = args.api_base.rstrip("/") + "/api/generate_note"

    _format = [x.strip() for x in args.format.split(",") if x.strip()]

    items = build_items()
    if args.only:
        items = [it for it in items if args.only in it["source"]]
    done_db = db_video_ids()
    done_prog = progress_success_ids()
    failed_prog = progress_failed_ids()
    skip = skip_bvs()

    def already_done(it: dict) -> bool:
        vid = it["video_id"]
        if not vid:
            return False
        if it["bv"] in skip:
            return True
        if vid in done_prog:
            return True
        # Pending BVs are explicitly requested; only a v2 SUCCESS skips them,
        # even if an older (possibly failed) task exists in the DB.
        if it["source"] == PENDING_LABEL:
            return False
        # A previous submission counts as done unless this driver recorded a
        # failure (then it is retried).
        ids = {vid}
        if "_p" not in vid:
            ids.add(vid + "_p1")
        return bool(ids & done_db) and vid not in failed_prog

    todo = [it for it in items if not already_done(it)]
    if args.limit:
        todo = todo[: args.limit]
    if args.verify:
        todo = todo[:1]

    skipped = len(items) - len(todo)
    log(f"[plan] sources={len(SOURCES)} pending={len(PENDING)} total={len(items)} "
        f"skipped={skipped} todo={len(todo)} concurrency={args.concurrency} "
        f"provider={args.provider} text={args.text_model} vision={args.vision_model}")

    models = [args.text_model]
    if any(it["vu"] for it in todo):
        models.append(args.vision_model)
    if args.check:
        return 0 if preflight(args.provider, models) else 2

    if args.dry_run:
        for it in todo[:20]:
            print(json.dumps({**it, "payload": payload(it, args.provider, args.text_model,
                                                       args.vision_model, _format, args.quality)},
                             ensure_ascii=False))
        log(f"[dry-run] {len(todo)} tasks would be submitted")
        return 0
    if not todo:
        log("[done] nothing to do")
        return 0
    if not args.skip_preflight and not preflight(args.provider, models):
        log("[abort] provider/model preflight failed; no tasks submitted")
        return 2

    wait_for_drain()

    pending = deque(todo)
    attempts: dict[str, int] = {}
    active: dict[str, dict] = {}
    changed: dict[str, float] = {}
    last_state: dict[str, str] = {}
    ok = err = done_n = 0
    total = len(todo)
    deadline = time.time() + args.budget_seconds if args.budget_seconds else None
    draining = False

    def fill() -> None:
        nonlocal err, draining
        if draining:
            return
        free_gb = shutil.disk_usage(BACKEND).free / 1e9
        if free_gb < args.min_free_gb:
            draining = True
            pending.clear()
            log(f"[disk] only {free_gb:.1f} GB free (< {args.min_free_gb} GB); "
                f"stopped submitting, draining in-flight tasks")
            return
        while pending and len(active) < args.concurrency:
            it = pending.popleft()
            body = payload(it, args.provider, args.text_model, args.vision_model,
                           _format, args.quality)
            tid = post(it, body)
            if not tid:
                attempts[it["video_id"]] = attempts.get(it["video_id"], 0) + 1
                if attempts[it["video_id"]] < args.max_attempts:
                    pending.append(it)
                else:
                    record({**it, "status": "FAILED", "error": "submit-failed"})
                    err += 1
                    log(f"[{done_n + err}/{total}] SUBMIT-FAIL {it['video_id']} ({it['source']})")
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
                    append_transcript(tid, it["video_id"])
                record({**it, "status": "SUCCESS", "task_id": tid})
                if not args.keep_media:
                    cleanup_media(it["video_id"])
                ok += 1
                done_n += 1
                log(f"[{done_n + err}/{total}] SUCCESS {it['video_id']} ({it['source']}) "
                    f"ok={ok} err={err}")
            elif s == "FAILED" or time.time() - changed[tid] > args.stall:
                it = active.pop(tid)
                attempts[it["video_id"]] = attempts.get(it["video_id"], 0) + 1
                if s == "FAILED" and attempts[it["video_id"]] < args.max_attempts:
                    pending.append(it)
                    log(f"[{done_n + err}/{total}] retry {attempts[it['video_id']]}/"
                        f"{args.max_attempts} {it['video_id']}")
                else:
                    record({**it, "status": "FAILED", "task_id": tid, "error": s})
                    err += 1
                    log(f"[{done_n + err}/{total}] FAILED {it['video_id']} ({it['source']}) "
                        f"state={s} ok={ok} err={err}")
        if pending or active:
            time.sleep(args.poll)

    log(f"[done] ok={ok} err={err} total={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
