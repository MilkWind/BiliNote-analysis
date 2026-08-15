#!/usr/bin/env python3
"""Check & complete duyi course notes against bcut transcriptions using DeepSeek.

- Maps each note to its BV id via the 视频原文地址 line; transcript loaded from
  backend/transcription_files/{BV}.txt (one-to-one, verified bijection).
- Model routing by audio duration (ffprobe on backend/download_audios/{BV}.mp3):
    >= 600s -> deepseek-v4-pro   (thinking enabled, reasoning_effort high)
    <  600s -> deepseek-v4-flash (thinking disabled)
- Concurrency caps default 32 (pro) / 64 (flash), far under DeepSeek's 500/2500.
- Response "笔记内容已完整，无需增改" -> note left untouched; otherwise the
  returned full note overwrites the original .md in place.
- Resume-safe via backend/note_check_state.json (successes only); failures of
  the latest run are written to backend/note_check_failed.txt.
- Usage: python script/check_complete_notes.py [--limit N] [--pro-workers N] [--flash-workers N]
"""
import concurrent.futures
import json
import random
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from openai import (
    OpenAI,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    BadRequestError,
    RateLimitError,
)

ROOT = Path(__file__).resolve().parents[1]
NOTES_DIR = Path(r"D:\development-projects\personal-projects\persional-knowledge\technology\frontend\duyi")
TRANS_DIR = ROOT / "transcription_files"
AUDIO_DIR = ROOT / "download_audios"
DB = ROOT / "bili_note.db"

STATE_FILE = ROOT / "note_check_state.json"
DURATIONS_FILE = ROOT / "note_check_durations.json"
FAILED_FILE = ROOT / "note_check_failed.txt"

MODEL_PRO = "deepseek-v4-pro"
MODEL_FLASH = "deepseek-v4-flash"
PRO_WORKERS_DEFAULT = 32
FLASH_WORKERS_DEFAULT = 64
DURATION_THRESHOLD = 600.0
SENTINEL = "笔记内容已完整，无需增改"
MAX_TOKENS = 16384
RETRY_DELAYS = [15, 45, 90]

FFPROBE = shutil.which("ffprobe") or r"D:\media-tools\ffmpeg-2026-08-06-git-essentials_build\bin\ffprobe.exe"

_state_lock = threading.Lock()

PROMPT_SYSTEM = (
    "你是一位严谨的前端课程笔记审校编辑。你的任务是根据音频转写文本核对并补全课程笔记，"
    "确保笔记完整、准确，且不破坏原有结构与视频帧相关的内容。"
)

PROMPT_USER_TMPL = """请比对【原始笔记】和【音频转写文本】，检查原始笔记中是否遗漏了音频转写文本中的关键内容，例如关键建议、重要知识、核心观点、重要示例与结论等。

要求：
1. 如果有遗漏：对原始笔记进行补充和修改，直接输出修改后的完整笔记；不要添加其它任何附带说明（包括开头、结尾的解释或修改说明）。
2. 如果没有遗漏：直接输出“{sentinel}”，不要输出其它任何内容。
3. 保持原始笔记的整体结构、标题层级、*Content-时间戳* 标记、视频来源/原文地址链接行与 Markdown 格式；不要无故重排、改写或删减原有内容。
4. 补充的内容应融入原有结构中合适的位置，风格与原笔记保持一致。
5. 重要提示：音频转写文本中不包含视频帧信息，那些存在于原始笔记而不存在于音频转写文本中的内容都是视频帧中的内容，你可以根据转写文本优化它们，但不要删除它们原本记录的信息。

===== 原始笔记 =====
{note}

===== 音频转写文本 =====
{transcript}"""


def parse_int_arg(name: str, default: int) -> int:
    for i, a in enumerate(sys.argv):
        if a == name and i + 1 < len(sys.argv):
            try:
                return int(sys.argv[i + 1])
            except ValueError:
                pass
    return default


def load_api_key() -> tuple:
    con = sqlite3.connect(DB)
    try:
        row = con.execute(
            "SELECT api_key, base_url FROM providers WHERE id = ?", ("deepseek",)
        ).fetchone()
    finally:
        con.close()
    if not row or not row[0]:
        raise SystemExit("deepseek provider/api_key not found in bili_note.db")
    return row[0], (row[1] or "https://api.deepseek.com").rstrip("/")


def extract_bv(text: str):
    m = re.search(r"视频原文地址[：:]\s*https?://\S*?(BV[0-9A-Za-z]{10})", text)
    if not m:
        m = re.search(r"(BV[0-9A-Za-z]{10})", text)
    return m.group(1) if m else None


def probe_durations(bvs: list) -> dict:
    cache = {}
    if DURATIONS_FILE.exists():
        try:
            cache = json.loads(DURATIONS_FILE.read_text(encoding="utf-8"))
        except Exception:
            cache = {}
    missing = [bv for bv in bvs if bv not in cache]
    for i, bv in enumerate(missing, 1):
        mp3 = AUDIO_DIR / f"{bv}.mp3"
        dur = 0.0
        if mp3.exists():
            try:
                out = subprocess.run(
                    [FFPROBE, "-v", "error", "-show_entries", "format=duration",
                     "-of", "csv=p=0", str(mp3)],
                    capture_output=True, text=True, timeout=30,
                )
                dur = float(out.stdout.strip())
            except Exception as exc:
                print(f"[warn] ffprobe failed for {bv}: {exc}", file=sys.stderr, flush=True)
        cache[bv] = dur
        if i % 100 == 0:
            DURATIONS_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    if missing:
        DURATIONS_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return cache


def strip_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines).strip()
    return t


def is_sentinel(body: str) -> bool:
    s = body.strip().strip("“”\"'`。 \n")
    return s == SENTINEL or (SENTINEL in s and len(s) <= len(SENTINEL) + 20)


def ensure_bv_link(body: str, bv: str, original: str) -> str:
    """Guarantee the 视频原文地址 link line survives the rewrite; re-inject it
    after the H1 title if the model dropped it."""
    if bv in body:
        return body
    m = re.search(r"^>.*" + bv + r".*$", original, re.M)
    link_line = m.group(0) if m else f"> 视频原文地址：https://www.bilibili.com/video/{bv}"
    lines = body.splitlines()
    if lines and lines[0].lstrip().startswith("# "):
        p = 2 if (len(lines) > 1 and lines[1].strip() == "") else 1
    else:
        p = 0
    lines[p:p] = [link_line, ""]
    return "\n".join(lines)


def process_note(client: OpenAI, note_path: Path, bv: str, duration: float, state: dict) -> tuple:
    transcript = (TRANS_DIR / f"{bv}.txt").read_text(encoding="utf-8").strip()
    original = note_path.read_text(encoding="utf-8")

    if duration >= DURATION_THRESHOLD:
        model, thinking, effort = MODEL_PRO, {"type": "enabled"}, "high"
    else:
        model, thinking, effort = MODEL_FLASH, {"type": "disabled"}, None

    messages = [
        {"role": "system", "content": PROMPT_SYSTEM},
        {"role": "user", "content": PROMPT_USER_TMPL.format(
            sentinel=SENTINEL, note=original, transcript=transcript)},
    ]
    params = {"model": model, "messages": messages, "stream": False, "max_tokens": MAX_TOKENS}
    extra: dict = {"thinking": thinking}
    if effort:
        extra["reasoning_effort"] = effort

    content = None
    last_exc = None
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            resp = client.chat.completions.create(**params, extra_body=dict(extra))
            content = (resp.choices[0].message.content or "").strip()
            if content:
                break
            raise ValueError("empty response content")
        except BadRequestError as exc:
            msg = str(exc).lower()
            if "max_tokens" in msg and "max_tokens" in params:
                params.pop("max_tokens")
                continue
            if ("thinking" in msg and "thinking" in extra) or ("reasoning" in msg and "reasoning_effort" in extra):
                extra.pop("thinking", None)
                extra.pop("reasoning_effort", None)
                continue
            raise
        except (RateLimitError, APIConnectionError, APITimeoutError) as exc:
            last_exc = exc
        except APIStatusError as exc:
            if exc.status_code is not None and exc.status_code >= 500:
                last_exc = exc
            else:
                raise
        if attempt < len(RETRY_DELAYS):
            delay = RETRY_DELAYS[attempt] + random.uniform(0, 10)
            print(f"[retry] {bv} attempt {attempt + 1} failed ({last_exc}); sleeping {delay:.0f}s",
                  file=sys.stderr, flush=True)
            time.sleep(delay)
    if not content:
        raise last_exc or RuntimeError("no response")

    body = strip_code_fences(content)
    if is_sentinel(body):
        status = "complete"
    else:
        if len(body) < max(300, int(len(original) * 0.25)):
            raise ValueError(f"suspiciously short response ({len(body)} chars vs original {len(original)}), keeping original")
        body = ensure_bv_link(body, bv, original)
        note_path.write_text(body if body.endswith("\n") else body + "\n", encoding="utf-8")
        status = "modified"

    with _state_lock:
        state[bv] = {
            "status": status,
            "model": model,
            "note": note_path.name,
            "at": datetime.now().isoformat(timespec="seconds"),
        }
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    return bv, status


def main() -> int:
    pro_workers = max(1, parse_int_arg("--pro-workers", PRO_WORKERS_DEFAULT))
    flash_workers = max(1, parse_int_arg("--flash-workers", FLASH_WORKERS_DEFAULT))
    limit = parse_int_arg("--limit", 0)

    api_key, base_url = load_api_key()
    client = OpenAI(api_key=api_key, base_url=base_url, max_retries=0)

    state = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    tasks = []
    for note_path in sorted(NOTES_DIR.rglob("*.md")):
        bv = extract_bv(note_path.read_text(encoding="utf-8", errors="replace"))
        if not bv:
            print(f"[skip] no BV id found in {note_path}", file=sys.stderr, flush=True)
            continue
        if bv in state:
            continue
        if not (TRANS_DIR / f"{bv}.txt").exists():
            print(f"[skip] transcript missing for {bv} ({note_path.name})", file=sys.stderr, flush=True)
            continue
        tasks.append((note_path, bv))
    if limit and limit > 0:
        tasks = tasks[:limit]

    durations = probe_durations(sorted({bv for _, bv in tasks}))
    pro_tasks = [(p, b) for p, b in tasks if durations.get(b, 0.0) >= DURATION_THRESHOLD]
    flash_tasks = [(p, b) for p, b in tasks if durations.get(b, 0.0) < DURATION_THRESHOLD]
    total = len(tasks)
    print(f"[plan] todo={total} pro={len(pro_tasks)} flash={len(flash_tasks)} "
          f"workers pro={pro_workers} flash={flash_workers}", file=sys.stderr, flush=True)
    if not tasks:
        return 0

    counters = {"done": 0, "modified": 0, "complete": 0}
    failures = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=pro_workers) as pro_pool, \
         concurrent.futures.ThreadPoolExecutor(max_workers=flash_workers) as flash_pool:
        futures = {}
        for p, b in pro_tasks:
            futures[pro_pool.submit(process_note, client, p, b, durations.get(b, 0.0), state)] = b
        for p, b in flash_tasks:
            futures[flash_pool.submit(process_note, client, p, b, durations.get(b, 0.0), state)] = b
        for fut in concurrent.futures.as_completed(futures):
            bv = futures[fut]
            try:
                _, status = fut.result()
                counters[status] += 1
            except Exception as exc:
                failures.append(bv)
                print(f"[FAIL] {bv}: {exc}", file=sys.stderr, flush=True)
            counters["done"] += 1
            if counters["done"] % 25 == 0 or counters["done"] == total:
                print(f"[progress] {counters['done']}/{total} modified={counters['modified']} "
                      f"complete={counters['complete']} failed={len(failures)}", file=sys.stderr, flush=True)

    prev_failed = set()
    if FAILED_FILE.exists():
        prev_failed = {ln.strip() for ln in FAILED_FILE.read_text(encoding="utf-8").splitlines() if ln.strip()}
    remaining_failed = sorted((prev_failed - set(state)) | set(failures))
    FAILED_FILE.write_text("\n".join(remaining_failed) + ("\n" if remaining_failed else ""),
                           encoding="utf-8")

    print(f"[done] modified={counters['modified']} complete={counters['complete']} "
          f"failed={len(failures)} (state total={len(state)})", file=sys.stderr, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
