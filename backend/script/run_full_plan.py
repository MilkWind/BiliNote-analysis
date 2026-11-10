#!/usr/bin/env python3
"""Unattended two-phase runner for the expanded note batch.

Phase 1 — Bilibili downloads with exactly 2 workers (the account/IP limit):
  pre-download every MP4 (video-understanding tasks) and MP3+.meta.json.

Phase 2 — Parsing with high concurrency:
  start a patched backend on port 8484 with TASK_MAX_WORKERS={WORKERS}, then run the
  batch driver at --concurrency {WORKERS} against it. All media is local, so only
  ASR/frame-extraction/LLM run during this phase; downloads hit the cache.

Worker count — do not raise blindly
-----------------------------------
Each parsing task runs FFmpeg frame extraction plus grid-image encoding. At 32
workers this machine exhausted the Windows commit limit (`WinError 1455 页面文件太小`)
and tasks failed with `视频处理失败`. 8 workers ran for ~20 hours with a 0.7 GB
backend footprint. Tune with the ``PHASE2_WORKERS`` environment variable (default
32, but 8 is the value that was proven stable here).

Pausing
-------
Set ``PAUSE_AT="YYYY-MM-DD HH:MM:SS"`` (local time) and the orchestrator stops
itself at that moment: it terminates the running download child, writes
``goal_videos/_full_plan_paused.flag`` and exits. Re-running clears the flag.
There is no resume flag needed — phase 1 and the driver both skip finished work.

Resume-safe: pre-download skips existing media; the driver skips DB/progress
SUCCESS tasks. Logs: goal_videos/_predownload_run.log,
goal_videos/_goal_notes_run_v2.log, goal_videos/_full_plan_run.log.

Usage (from backend/):
    python script/run_full_plan.py                    # phases 1 -> 2, unattended
    PHASE2_WORKERS=8 python script/run_full_plan.py   # safer, proven configuration
    PAUSE_AT="2026-11-07 05:00:00" python script/run_full_plan.py

Preconditions: ``goal_videos/<source>.txt`` lists built by
``pagination_query/build_goal_video_lists.py``, a valid Bilibili cookie in
``backend/config/downloader.json``, and Ark credentials in ``.env``.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import threading
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
GOAL = ROOT / "goal_videos"
LOG = GOAL / "_full_plan_run.log"
STOP_FLAG = GOAL / "_full_plan_paused.flag"
load_dotenv(BACKEND / ".env")

sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "script"))

import batch_goal_notes_v2 as drv  # noqa: E402
import predownload_goal_media as pre  # noqa: E402

PYTHON = sys.executable
PORT = 8484
MAX_MISSING = 200
# Below this, the remainder is almost always deleted/geo-blocked videos; phase 2
# can absorb them instead of looping download passes forever.
PHASE1_ENOUGH = 10
MAX_PASSES = 6
# Ark allows 500 RPM / 1M TPM, so 32 concurrent tasks is ample; 64 workers were
# observed to put the host under memory pressure (each task runs FFmpeg frame
# extraction plus grid-image encoding).
WORKERS = int(os.getenv("PHASE2_WORKERS", "32"))
PREDOWNLOAD_PID: int | None = None
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def pause_deadline() -> float | None:
    """Wall-clock deadline from PAUSE_AT (local 'YYYY-MM-DD HH:MM[:SS]'), if set."""
    raw = os.getenv("PAUSE_AT", "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return time.mktime(time.strptime(raw, fmt))
        except ValueError:
            continue
    log(f"[pause] ignoring unparseable PAUSE_AT={raw!r}")
    return None


def pause_watcher(deadline: float) -> None:
    """Stop any running predownload child at the deadline, then stop the orchestrator."""
    while time.time() < deadline:
        time.sleep(10)
    log(f"[pause] deadline reached; stopping the pipeline")
    stop_predownload_children()
    STOP_FLAG.write_text(str(time.time()), encoding="utf-8")
    log("[pause] orchestrator stopping; rerun run_full_plan.py to resume")
    os._exit(0)


def stop_predownload_children() -> None:
    """Terminate predownload_goal_media.py processes started by this run.

    Uses tasklist + CIM via PowerShell: wmic is not present on recent Windows
    builds, and its absence must not leave downloads running past a pause.
    """
    if PREDOWNLOAD_PID:
        log(f"[pause] terminating predownload pid={PREDOWNLOAD_PID}")
        subprocess.run(["taskkill", "/PID", str(PREDOWNLOAD_PID), "/F", "/T"],
                       capture_output=True, text=True, timeout=15)
        return
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"],
            capture_output=True, text=True, timeout=30,
        ).stdout
        rows = json.loads(out or "[]")
    except Exception as e:  # noqa: BLE001
        log(f"[pause] could not list processes: {e}")
        return
    if isinstance(rows, dict):
        rows = [rows]
    for row in rows:
        cmd = row.get("CommandLine") or ""
        if "predownload_goal_media.py" not in cmd:
            continue
        pid = row.get("ProcessId")
        log(f"[pause] terminating predownload pid={pid}")
        subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"],
                       capture_output=True, text=True, timeout=15)


def child_env() -> dict:
    env = os.environ.copy()
    env["BILINOTE_VIDEO_MAX_HEIGHT"] = "720"
    env["BACKEND_PORT"] = str(PORT)
    env["TASK_MAX_WORKERS"] = str(WORKERS)
    return env


def missing_media() -> tuple[int, int]:
    items = drv.build_items()
    done_prog = drv.progress_success_ids()
    db = drv.db_video_ids()
    skip = drv.skip_bvs()
    todo = [it for it in items if not pre.already_done(it, done_prog, db, skip)
            and not pre.media_ready(it)]
    return len(todo), len(items)


def backend_ready() -> bool:
    try:
        with urllib.request.urlopen(f"http://localhost:{PORT}/api/get_all_providers", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def network_ok() -> bool:
    """True if DNS works and Bilibili's host answers at all.

    Any HTTP status (200, 412, 403...) proves the link is up; only DNS or
    connection failures mean the network is actually down. Bilibili answers
    412 to header-less requests, which is an HTTPError but still "reachable".
    """
    try:
        socket.gethostbyname("www.bilibili.com")
    except Exception:
        return False
    req = urllib.request.Request(
        "https://api.bilibili.com/x/web-interface/nav",
        headers={"User-Agent": UA, "Referer": "https://www.bilibili.com/"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status < 500
    except urllib.error.HTTPError as e:
        return e.code < 500
    except Exception:
        return False


def wait_for_network(max_minutes: int = 30) -> bool:
    deadline = time.time() + max_minutes * 60
    while time.time() < deadline:
        if network_ok():
            return True
        log(f"[network] Bilibili unreachable; retrying in 60s")
        time.sleep(60)
    return False


def start_backend() -> None:
    if backend_ready():
        log(f"backend :{PORT} already running; reusing")
        return
    log(f"starting backend :{PORT} (TASK_MAX_WORKERS={WORKERS}, video<=720p)")
    out = open(BACKEND / "logs" / "backend_8484_console.log", "a", encoding="utf-8")
    subprocess.Popen([PYTHON, "main.py"], cwd=BACKEND, env=child_env(),
                     stdout=out, stderr=subprocess.STDOUT)
    for _ in range(60):
        time.sleep(2)
        if backend_ready():
            log(f"backend :{PORT} ready")
            return
    raise SystemExit("backend :8484 did not become ready")


def main() -> int:
    log("=== full plan start ===")
    if STOP_FLAG.exists():
        STOP_FLAG.unlink()
        log("[pause] cleared stale pause flag")

    deadline = pause_deadline()
    if deadline:
        if deadline <= time.time():
            log(f"[pause] PAUSE_AT={os.getenv('PAUSE_AT')} is in the past; ignoring")
        else:
            log(f"[pause] will pause at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(deadline))}")
            threading.Thread(target=pause_watcher, args=(deadline,), daemon=True).start()

    repeats = 0
    for pass_no in range(1, MAX_PASSES + 1):
        if STOP_FLAG.exists():
            log("[pause] stop flag present; not starting another download pass")
            return 0
        missing, total = missing_media()
        log(f"[phase1] pass {pass_no}: missing_media={missing}/{total}")
        # Stop retrying once the remainder is small enough for phase 2 to absorb;
        # the last few items are usually deleted/geo-blocked and never resolve.
        if missing <= PHASE1_ENOUGH:
            log(f"[phase1] only {missing} item(s) missing (<= {PHASE1_ENOUGH}); "
                f"skipping further download passes")
            break
        if not wait_for_network():
            log("[network] still unreachable after waiting; stopping without burning the queue")
            return 4
        global PREDOWNLOAD_PID
        proc = subprocess.Popen([PYTHON, "script/predownload_goal_media.py", "--workers", "2"],
                                cwd=BACKEND, env=child_env())
        PREDOWNLOAD_PID = proc.pid
        proc.wait()
        PREDOWNLOAD_PID = None
        if STOP_FLAG.exists():
            log("[pause] stopped during download pass; will resume on next run")
            return 0
        new_missing = missing_media()[0]
        log(f"[phase1] pass {pass_no} done: missing_media={new_missing}/{total}")
        # A pass that makes no progress twice in a row means the rest are
        # permanently unavailable; stop looping.
        if new_missing >= missing:
            repeats += 1
            if repeats >= 2:
                log(f"[phase1] no progress for {repeats} passes; treating the remaining "
                    f"{new_missing} as permanently unavailable")
                break
        else:
            repeats = 0
        missing, taken = new_missing, taken
        time.sleep(60)

    missing, total = missing_media()
    if missing > MAX_MISSING:
        log(f"[abort] {missing} media files still missing (> {MAX_MISSING}); "
            f"not starting phase 2 with {WORKERS} concurrent downloads")
        return 3
    if missing:
        log(f"[warn] {missing} media files missing; phase 2 may download these at high concurrency")

    log("[phase2] starting high-concurrency parsing")
    start_backend()
    cmd = [PYTHON, "script/batch_goal_notes_v2.py",
           "--api-base", f"http://localhost:{PORT}",
           "--concurrency", str(WORKERS), "--poll", "20", "--stall", "7200"]
    rc = subprocess.run(cmd, cwd=BACKEND, env=child_env()).returncode
    log(f"[phase2] driver exited rc={rc}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
