#!/usr/bin/env python3
"""Pre-download media for the v2 note batch.

Downloads, for every task that is not already completed:
  * the full MP4 for video_understanding tasks,
  * the MP3 + .meta.json for every task (the patched BilibiliDownloader reuses both).

The backend's NoteGenerator will then hit the local cache instead of downloading
during generation, so the LLM/ASR pipeline can run at high concurrency.

Resume-safe: skips media that already exists. Writes failures to
goal_videos/_predownload_failures.txt and progress to _predownload_progress.jsonl.

Worker count matters
--------------------
Bilibili throttles concurrent downloads from one account: 8 workers were measured
at ~8 KiB/s each with frequent CDN read timeouts, while 2 workers sustain
~0.5 MB/s. Keep ``--workers 2`` unless you know the account has headroom.

Video size
----------
Video-understanding frames are downscaled to 960x540 cells, so 1080p sources are
wasteful. ``BILINOTE_VIDEO_MAX_HEIGHT`` (read from .env) caps the download
height, e.g. ``BILINOTE_VIDEO_MAX_HEIGHT=720``; unset means best available.

Safety
------
* ``--min-free-gb`` stops starting new downloads when the disk gets tight.
* ``--net-fail-limit`` aborts the pass after N consecutive network-level errors
  (DNS failure, connection reset) so an outage cannot burn through the queue.

Media lands in ``backend/data/data`` as ``<video_id>.mp4`` / ``.mp3`` / ``.meta.json``
where ``video_id`` is ``BV...`` or ``BV..._pN``.

Usage (from backend/):
    python script/predownload_goal_media.py --workers 2
    python script/predownload_goal_media.py --only 前端小码哥 --limit 5
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND / ".env")
ROOT = BACKEND.parent
GOAL = ROOT / "goal_videos"
DATA_DIR = BACKEND / "data" / "data"
PROGRESS = GOAL / "_predownload_progress.jsonl"
FAILURES = GOAL / "_predownload_failures.txt"
LOG = GOAL / "_predownload_run.log"

sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "script"))

import batch_goal_notes_v2 as drv  # noqa: E402
from app.downloaders.bilibili_downloader import BilibiliDownloader  # noqa: E402

_tls = threading.local()
_stop = threading.Event()
_lock = threading.Lock()


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with _lock:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def get_downloader() -> BilibiliDownloader:
    d = getattr(_tls, "downloader", None)
    if d is None:
        d = BilibiliDownloader()
        _tls.downloader = d
    return d


def _is_network_error(status: str) -> bool:
    """DNS / connection failures mean the whole link is down, not one video."""
    markers = ("getaddrinfo failed", "Failed to resolve", "Name or service not known",
               "ConnectionError", "ConnectionResetError", "Network is unreachable",
               "Temporary failure in name resolution", "Max retries exceeded")
    return any(m in status for m in markers)


def media_ready(it: dict) -> bool:
    vid = it["video_id"]
    if not vid:
        return True
    if it["vu"] and not (DATA_DIR / f"{vid}.mp4").exists():
        return False
    if not (DATA_DIR / f"{vid}.mp3").exists():
        return False
    if not (DATA_DIR / f"{vid}.meta.json").exists():
        return False
    return True


def download_one(it: dict) -> tuple[str, str]:
    """Returns (video_id, status)."""
    if _stop.is_set():
        return it["video_id"], "skipped-disk"
    vid = it["video_id"]
    if not vid:
        return "", "skipped-noid"
    d = get_downloader()
    try:
        if it["vu"] and not (DATA_DIR / f"{vid}.mp4").exists():
            d.download_video(it["url"], output_dir=str(DATA_DIR))
        if not (DATA_DIR / f"{vid}.mp3").exists() or not (DATA_DIR / f"{vid}.meta.json").exists():
            d.download(it["url"], output_dir=str(DATA_DIR), quality="fast")
        return vid, "ok"
    except Exception as e:  # noqa: BLE001
        return vid, f"fail: {type(e).__name__}: {str(e)[:200]}"


def already_done(it: dict, done_prog: set[str], db: set[str], skip: set[str]) -> bool:
    vid = it["video_id"]
    if not vid:
        return True
    if it["bv"] in skip or vid in done_prog:
        return True
    if it["source"] == drv.PENDING_LABEL:
        return False
    ids = {vid}
    if "_p" not in vid:
        ids.add(vid + "_p1")
    return bool(ids & db)


def main() -> int:
    ap = argparse.ArgumentParser(description="Pre-download batch media")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--min-free-gb", type=float, default=50.0)
    ap.add_argument("--net-fail-limit", type=int, default=20,
                    help="abort the pass after this many consecutive network-level failures")
    args = ap.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    items = drv.build_items()
    if args.only:
        items = [it for it in items if args.only in it["source"]]
    done_prog = drv.progress_success_ids()
    db = drv.db_video_ids()
    skip = drv.skip_bvs()
    todo = [it for it in items if not already_done(it, done_prog, db, skip) and not media_ready(it)]
    if args.limit:
        todo = todo[: args.limit]

    log(f"[plan] total={len(items)} todo_media={len(todo)} workers={args.workers} "
        f"free_gb={shutil.disk_usage(DATA_DIR).free / 1e9:.1f}")

    global _stop
    _stop = threading.Event()

    ok = fail = net_fail = 0
    failures: list[tuple[str, str]] = []
    start = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {}
        for it in todo:
            if shutil.disk_usage(DATA_DIR).free / 1e9 < args.min_free_gb:
                log(f"[disk] free space below {args.min_free_gb} GB; stopping new downloads")
                _stop.set()
                break
            if _stop.is_set():
                break
            futs[ex.submit(download_one, it)] = it
        for i, f in enumerate(as_completed(futs), 1):
            vid, status = f.result()
            if status == "ok":
                ok += 1
            elif status.startswith("fail"):
                fail += 1
                failures.append((vid, status))
                log(f"[FAIL] {vid}: {status}")
                if _is_network_error(status):
                    net_fail += 1
                    if net_fail >= args.net_fail_limit:
                        log(f"[network] {net_fail} consecutive network errors; "
                            f"aborting pass so the rest can be retried later")
                        _stop.set()
                        for pending_f in futs:
                            pending_f.cancel()
                        break
                else:
                    net_fail = 0
            if i % 20 == 0 or i == len(futs):
                elapsed = max(time.time() - start, 1)
                log(f"[progress] {i}/{len(futs)} ok={ok} fail={fail} "
                    f"({i / elapsed * 60:.1f} tasks/min)")

    if failures:
        with FAILURES.open("a", encoding="utf-8") as f:
            for vid, status in failures:
                f.write(f"{vid}\t{status}\n")
    log(f"[done] ok={ok} fail={fail} skipped={len(todo) - ok - fail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
