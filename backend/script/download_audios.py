#!/usr/bin/env python3
"""Download audio (mp3) for every BV link in goal_videos/渡一.txt into backend/download_audios.

- Reads the bilibili cookie from script/bilibili/pagination_query/fetch_config.json
  (Netscape cookiefile injected into yt-dlp, same as BilibiliDownloader).
- Output files are named <BV>.mp3; already-existing files are skipped (resume-safe).
- Failures are appended to backend/download_audios_failed.txt (one URL per line).
"""
import json
import re
import sys
import time
import tempfile
from pathlib import Path

import yt_dlp

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT.parent / "goal_videos" / "渡一.txt"
CONFIG = ROOT / "script" / "bilibili" / "pagination_query" / "fetch_config.json"
OUT = ROOT / "download_audios"
FAILED_LOG = ROOT / "download_audios_failed.txt"

FORMAT = "bestaudio[ext=m4a]/bestaudio/best"


def bv_id(url: str) -> str:
    m = re.search(r"BV([0-9A-Za-z]+)", url)
    return f"BV{m.group(1)}" if m else url.rstrip("/").rsplit("/", 1)[-1]


def write_cookiefile(cookie: str) -> str:
    lines = ["# Netscape HTTP Cookie File\n"]
    for pair in cookie.split("; "):
        if "=" in pair:
            key, value = pair.split("=", 1)
            lines.append(f".bilibili.com\tTRUE\t/\tFALSE\t0\t{key}\t{value}\n")
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    tmp.writelines(lines)
    tmp.close()
    return tmp.name


def parse_limit() -> int:
    for i, a in enumerate(sys.argv):
        if a == "--limit" and i + 1 < len(sys.argv):
            try:
                return int(sys.argv[i + 1])
            except ValueError:
                return 0
    return 0


def main() -> int:
    limit = parse_limit()
    urls = [ln.strip() for ln in INPUT.read_text(encoding="utf-8").splitlines() if ln.strip()]
    OUT.mkdir(parents=True, exist_ok=True)

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    cookiefile = write_cookiefile(cfg["bilibili"]["cookie"])

    existing = {p.stem for p in OUT.glob("*.mp3")}
    todo = [u for u in urls if bv_id(u) not in existing]
    already_done = len(urls) - len(todo)
    if limit and limit > 0:
        todo = todo[:limit]

    print(f"[plan] total={len(urls)} already_done={already_done} todo={len(todo)}", file=sys.stderr, flush=True)

    ok = err = 0
    for i, url in enumerate(todo, 1):
        bid = bv_id(url)
        ydl_opts = {
            "format": FORMAT,
            "outtmpl": str(OUT / f"{bid}.%(ext)s"),
            "http_headers": {"Referer": "https://www.bilibili.com"},
            "noplaylist": True,
            "quiet": False,
            "cookiefile": cookiefile,
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "64"}
            ],
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
            ok += 1
            print(f"[{i}/{len(todo)}] OK {bid}", file=sys.stderr, flush=True)
        except Exception as exc:
            err += 1
            with FAILED_LOG.open("a", encoding="utf-8") as f:
                f.write(url + "\n")
            print(f"[{i}/{len(todo)}] FAIL {bid}: {exc}", file=sys.stderr, flush=True)
        time.sleep(3)

    print(f"[done] ok={ok} err={err}", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
