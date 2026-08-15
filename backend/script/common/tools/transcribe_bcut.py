#!/usr/bin/env python3
"""Upload backend/download_audios/*.mp3 to bcut (Bilibili ASR) in parallel and save
full transcript text to backend/transcription_files/{BV}.txt.

- Reuses BcutTranscriber upload/task/query primitives from app/transcriber/bcut.py.
- Default 3 parallel workers (--workers N to override, --limit N for test runs).
- Rate-limit safety:
    * global pacer spaces upload starts >= 2s apart (+jitter);
    * polling runs at 4s + jitter per file (not 1s), keeping aggregate QPS low;
    * a 412/429 on polling does NOT discard the task: a global circuit breaker
      pauses all polling for 60s (+extension), then polling resumes on the same
      task (the task stays valid server-side; re-upload is only used as a last
      resort via the 3-attempt outer retry with 60s/120s backoff).
- Resume-safe: skips BVs whose .txt already exists in transcription_files.
- Failures are appended to backend/transcription_failed.txt (one BV per line).
"""
import json
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.transcriber.bcut import BcutTranscriber  # noqa: E402

AUDIO_DIR = ROOT / "download_audios"
OUT_DIR = ROOT / "transcription_files"
FAILED_LOG = ROOT / "transcription_failed.txt"

PACE_INTERVAL = 2.0
POLL_INTERVAL = 4.0
POLL_TIMEOUT = 900.0
PAUSE_SECONDS = 60.0
MAX_ATTEMPTS = 3
BACKOFFS = [60, 120]

_pace_lock = threading.Lock()
_last_start = 0.0
_pause_until = 0.0
_pause_lock = threading.Lock()


def parse_arg(name: str, default: int) -> int:
    for i, a in enumerate(sys.argv):
        if a == name and i + 1 < len(sys.argv):
            try:
                return int(sys.argv[i + 1])
            except ValueError:
                pass
    return default


def pace() -> None:
    """Serialize upload starts across workers: wait until PACE_INTERVAL + jitter
    has elapsed since the previous worker started its upload."""
    global _last_start
    with _pace_lock:
        wait = _last_start + PACE_INTERVAL + random.uniform(0, 1.0) - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_start = time.monotonic()


def trip_pause() -> None:
    """Circuit breaker: extend the global polling pause."""
    with _pause_lock:
        global _pause_until
        _pause_until = max(_pause_until, time.monotonic() + PAUSE_SECONDS)


def wait_for_pause() -> None:
    with _pause_lock:
        remain = _pause_until - time.monotonic()
    if remain > 0:
        time.sleep(remain + random.uniform(0, 2.0))


def poll_result(transcriber: BcutTranscriber) -> dict:
    """Poll task/result until done, tolerating 412/429 via the global pause."""
    deadline = time.monotonic() + POLL_TIMEOUT
    while True:
        if time.monotonic() > deadline:
            raise TimeoutError(f"polling exceeded {POLL_TIMEOUT:.0f}s")
        wait_for_pause()
        try:
            resp = transcriber._query_result()
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 0
            if status in (412, 429):
                print(f"[412] rate-limited on poll, pausing all polling {PAUSE_SECONDS:.0f}s "
                      f"(task {transcriber.task_id})", file=sys.stderr, flush=True)
                trip_pause()
                continue
            raise
        state = resp.get("state")
        if state == 4:
            return resp
        if state == 3:
            raise RuntimeError(f"ASR task failed, state=3 (task {transcriber.task_id})")
        time.sleep(POLL_INTERVAL + random.uniform(0, 2.0))


def transcribe_one(mp3: Path) -> tuple:
    bv = mp3.stem
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            pace()
            transcriber = BcutTranscriber()
            transcriber._upload(str(mp3))
            transcriber._create_task()
            task_resp = poll_result(transcriber)
            result_json = json.loads(task_resp["result"])
            text = " ".join(
                u.get("transcript", "").strip()
                for u in result_json.get("utterances", [])
                if u.get("transcript", "").strip()
            )
            if not text:
                raise ValueError("empty transcript")
            (OUT_DIR / f"{bv}.txt").write_text(text, encoding="utf-8")
            return bv, True, ""
        except Exception as exc:
            if attempt < MAX_ATTEMPTS:
                delay = BACKOFFS[attempt - 1] + random.uniform(0, 30)
                print(f"[retry] {bv} attempt {attempt} failed: {exc}; sleeping {delay:.0f}s",
                      file=sys.stderr, flush=True)
                time.sleep(delay)
            else:
                return bv, False, str(exc)
    return bv, False, "unreachable"


def main() -> int:
    workers = max(1, parse_arg("--workers", 3))
    limit = parse_arg("--limit", 0)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mp3s = sorted(AUDIO_DIR.glob("*.mp3"))
    done = {p.stem for p in OUT_DIR.glob("*.txt")}
    todo = [p for p in mp3s if p.stem not in done]
    already = len(mp3s) - len(todo)
    if limit and limit > 0:
        todo = todo[:limit]

    print(f"[plan] total={len(mp3s)} already_done={already} todo={len(todo)} workers={workers}",
          file=sys.stderr, flush=True)
    if not todo:
        return 0

    ok = err = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(transcribe_one, p): p.stem for p in todo}
        for i, fut in enumerate(as_completed(futures), 1):
            bv, success, msg = fut.result()
            if success:
                ok += 1
                print(f"[{i}/{len(todo)}] OK {bv}", file=sys.stderr, flush=True)
            else:
                err += 1
                with FAILED_LOG.open("a", encoding="utf-8") as f:
                    f.write(bv + "\n")
                print(f"[{i}/{len(todo)}] FAIL {bv}: {msg}", file=sys.stderr, flush=True)

    print(f"[done] ok={ok} err={err}", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
