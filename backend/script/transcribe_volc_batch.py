#!/usr/bin/env python3
"""Batch-download + transcribe (Volc SeedASR) every video in
goal_videos/血狼破军.txt, writing only manuscripts (no notes) to
backend/note_results/{Video title}.md

Workflow
--------
1. Read "BV<id>\\t<title>" rows from goal_videos/血狼破军.txt.
2. Download missing audio into backend/download_audios/{BV}.mp3 via the app's
   BilibiliDownloader (reads the updated cookie from backend/config/downloader.json).
3. Transcribe each mp3 with VolcSeedAsrTranscriber (env VOLC_SEEDASR_API_KEY,
   loaded from the repo-root .env).
4. Write a readable Markdown manuscript per video under backend/note_results.

Concurrency / safety
--------------------
- Downloads capped at 2 workers + a global 1.5s start pacer (Bilibili 412 risk).
- Transcription capped at 4 workers (Volc SeedASR is an async API; retries with
  60/120s backoff on submit/poll failures).
- Transcription begins as soon as each audio finishes downloading.
- Resume-safe: already-written manuscripts are skipped.

Usage
-----
    python script/transcribe_volc_batch.py [--limit N]
"""
import json
import os
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import yt_dlp  # noqa: F401  (ensure available before app import)

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
INPUT = REPO / "goal_videos" / "血狼破军.txt"
AUDIO_DIR = ROOT / "download_audios"
NOTE_DIR = ROOT / "note_results"
STATE_FILE = ROOT / "transcribe_volc_state.json"
FAILED_FILE = ROOT / "transcribe_volc_failed.txt"

DL_WORKERS = 2
TR_WORKERS = 4
DL_PACE = 1.5
MAX_ATTEMPTS = 3
BACKOFFS = [60, 120]

sys.path.insert(0, str(ROOT))

BAD_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_state_lock = threading.Lock()

_pace_lock = threading.Lock()
_last_dl_start = 0.0


def load_root_env() -> None:
    env_file = REPO / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_limit() -> int:
    for i, a in enumerate(sys.argv):
        if a == "--limit" and i + 1 < len(sys.argv):
            try:
                return int(sys.argv[i + 1])
            except ValueError:
                return 0
    return 0


def sanitize(name: str) -> str:
    name = BAD_CHARS.sub("_", name)
    return name.strip().rstrip(".") or "unnamed"


def load_items() -> list:
    if not INPUT.exists():
        raise SystemExit(f"input not found: {INPUT}")
    items = []
    for line in INPUT.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t", 1)
        bv = parts[0].strip()
        title = parts[1].strip() if len(parts) > 1 else bv
        if re.fullmatch(r"BV[0-9A-Za-z]{10}", bv):
            items.append({"bv": bv, "title": title, "url": f"https://www.bilibili.com/video/{bv}"})
    return items


def manuscript_path(item: dict) -> Path:
    return NOTE_DIR / f"{sanitize(item['title'])}.md"


def record_state(state: dict) -> None:
    with _state_lock:
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")


def record_failure(bv: str) -> None:
    with _state_lock:
        with FAILED_FILE.open("a", encoding="utf-8") as f:
            f.write(bv + "\n")


def pace_download() -> None:
    global _last_dl_start
    with _pace_lock:
        wait = _last_dl_start + DL_PACE + random.uniform(0, 0.5) - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_dl_start = time.monotonic()


def download_job(item: dict) -> dict:
    """Download mp3 for one BV; returns a tagged result dict."""
    bv = item["bv"]
    mp3 = AUDIO_DIR / f"{bv}.mp3"
    if mp3.exists() and mp3.stat().st_size > 0:
        return {"kind": "dl", "bv": bv, "mp3": mp3, "err": None}

    pace_download()

    try:
        from app.downloaders.bilibili_downloader import BilibiliDownloader
        from app.enmus.note_enums import DownloadQuality

        result = BilibiliDownloader().download(
            video_url=item["url"],
            output_dir=str(AUDIO_DIR),
            quality=DownloadQuality.fast,
        )
        path = Path(result.file_path)
        if (not path.exists() or path.stat().st_size <= 0) and (not mp3.exists() or mp3.stat().st_size <= 0):
            raise FileNotFoundError(f"downloaded audio missing: {path}")
        final = path if path.exists() and path.stat().st_size > 0 else mp3
        return {"kind": "dl", "bv": bv, "mp3": final, "err": None}
    except Exception as exc:
        return {"kind": "dl", "bv": bv, "mp3": None, "err": str(exc)}


def transcribe_job(item: dict, state: dict) -> dict:
    """Transcribe audio via Volc SeedASR and write manuscript; returns tagged dict."""
    bv = item["bv"]
    mp3 = AUDIO_DIR / f"{bv}.mp3"
    if not mp3.exists() or mp3.stat().st_size <= 0:
        return {"kind": "tr", "bv": bv, "ok": False, "msg": "audio file missing"}

    from app.transcriber.volc_seedasr import VolcSeedAsrTranscriber

    last_exc = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            transcriber = VolcSeedAsrTranscriber()
            transcript = transcriber.transcript(file_path=str(mp3))
            if not transcript.segments:
                raise ValueError("empty transcript result")

            paragraphs = []
            buf = []
            buf_len = 0
            for seg in transcript.segments:
                text = (seg.text or "").strip()
                if not text:
                    continue
                buf.append(text)
                buf_len += len(text)
                if buf_len >= 180 and text[-1] in "。！？…!?；":
                    paragraphs.append("".join(buf))
                    buf, buf_len = [], 0
            if buf:
                paragraphs.append("".join(buf))

            body = "\n\n".join(paragraphs) if paragraphs else (transcript.full_text or "")

            md = [
                f"# {item['title']}",
                "",
                f"> 视频地址：https://www.bilibili.com/video/{bv}",
                f"> 转写时间：{datetime.now().isoformat(timespec='seconds')}",
                "",
                "## 转写文稿",
                "",
                body,
                "",
            ]
            out = manuscript_path(item)
            out.write_text("\n".join(md), encoding="utf-8")

            with _state_lock:
                state[bv] = {"title": item["title"], "ok": True, "file": out.name,
                             "at": datetime.now().isoformat(timespec="seconds")}
            record_state(state)
            return {"kind": "tr", "bv": bv, "ok": True, "msg": ""}
        except Exception as exc:
            last_exc = exc
            if attempt < MAX_ATTEMPTS:
                delay = BACKOFFS[attempt - 1] + random.uniform(0, 30)
                print(f"[retry] {bv} attempt {attempt} failed: {exc}; sleeping {delay:.0f}s",
                      file=sys.stderr, flush=True)
                time.sleep(delay)
    with _state_lock:
        state[bv] = {"title": item["title"], "ok": False, "error": str(last_exc),
                     "at": datetime.now().isoformat(timespec="seconds")}
    record_state(state)
    record_failure(bv)
    return {"kind": "tr", "bv": bv, "ok": False, "msg": str(last_exc)}


def main() -> int:
    load_root_env()
    limit = parse_limit()

    NOTE_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    items = load_items()
    if limit and limit > 0:
        items = items[:limit]

    done_files = {p.stem for p in NOTE_DIR.glob("*.md")}
    state = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    todo = []
    skipped = 0
    for it in items:
        if manuscript_path(it).stem in done_files and state.get(it["bv"], {}).get("ok"):
            skipped += 1
            continue
        todo.append(it)

    print(f"[plan] total={len(items)} skipped={skipped} todo={len(todo)} "
          f"dl_workers={DL_WORKERS} tr_workers={TR_WORKERS}", file=sys.stderr, flush=True)
    if not todo:
        return 0

    counters = {"dl_ok": 0, "dl_err": 0, "tr_ok": 0, "tr_err": 0}
    pending = set()

    with ThreadPoolExecutor(max_workers=DL_WORKERS) as dl_pool, \
         ThreadPoolExecutor(max_workers=TR_WORKERS) as tr_pool:
        for it in todo:
            pending.add(dl_pool.submit(download_job, it))

        while pending:
            for fut in as_completed(tuple(pending)):
                pending.discard(fut)
                try:
                    res = fut.result()
                except Exception as exc:
                    print(f"[err] future failed: {exc}", file=sys.stderr, flush=True)
                    continue
                if res["kind"] == "dl":
                    bv, err = res["bv"], res["err"]
                    if res["mp3"] is None or err:
                        counters["dl_err"] += 1
                        record_failure(bv)
                        print(f"[dl-FAIL] {bv}: {err}", file=sys.stderr, flush=True)
                        continue
                    counters["dl_ok"] += 1
                    item = next((x for x in todo if x["bv"] == bv), None)
                    if item:
                        pending.add(tr_pool.submit(transcribe_job, item, state))
                else:
                    if res["ok"]:
                        counters["tr_ok"] += 1
                        print(f"[tr-OK] {res['bv']} (tr_ok={counters['tr_ok']})", file=sys.stderr, flush=True)
                    else:
                        counters["tr_err"] += 1
                        print(f"[tr-FAIL] {res['bv']}: {res['msg']}", file=sys.stderr, flush=True)
            print(f"[progress] dl_ok={counters['dl_ok']} dl_err={counters['dl_err']} "
                  f"tr_ok={counters['tr_ok']} tr_err={counters['tr_err']}", file=sys.stderr, flush=True)

    print(f"[done] dl_ok={counters['dl_ok']} dl_err={counters['dl_err']} "
          f"tr_ok={counters['tr_ok']} tr_err={counters['tr_err']}", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
