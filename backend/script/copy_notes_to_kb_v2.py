#!/usr/bin/env python3
"""Copy the v2 batch notes from note_results/ into the persional-knowledge repo.

Each source UP gets one folder under ``notes/<category>/<UP>/``. The filename is
taken from the video title in ``{task_id}.json`` (``audio_meta.title``), because
most generated notes have no ``# `` heading of their own.

Multi-part videos carry a title of the form ``"<video title> pNN <part title>"``;
the part title alone is used, prefixed with a short slice of the video title when
the part name is generic (前言 / 导学 / …).

Notes are copied verbatim (the appended ``## 文稿转写`` transcript stays inline).
Existing files are never overwritten: a differing note with the same title gets a
``(2)``, ``(3)`` … suffix, and an identical file is skipped.

Idempotency
-----------
``goal_videos/_kb_copy_state.json`` maps ``video_id -> relative path``. A re-run
compares the recorded file to the source and skips when identical, so running
twice is safe. It also records every copy in ``_kb_copy_report.md`` (per source,
per destination, suffixed collisions, anomalies).

Orphan notes
------------
The batch driver only writes a progress line when it observes SUCCESS, so tasks
that finished during a crash or between polls leave a note with no record.
``--include-orphans`` scans ``note_results/*_markdown.md`` for those, routes them
by their yt-dlp ``uploader`` and copies them too. Without the flag they are
silently skipped.

Adapting to a new batch
-----------------------
Edit ``TARGETS`` (source label -> folder under ``notes/``); sources missing from
it are counted as ``unmapped`` and not copied. ``STANDALONE`` handles one-off
videos that have no UP folder — they go to a ``_散装视频`` folder.

Usage (from backend/):
    python script/copy_notes_to_kb_v2.py --dry-run
    python script/copy_notes_to_kb_v2.py
    python script/copy_notes_to_kb_v2.py --only 渡一
    python script/copy_notes_to_kb_v2.py --include-orphans     # after a crash
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
GOAL = ROOT / "goal_videos"
PROGRESS = GOAL / "_goal_notes_progress_v2.jsonl"
NOTE_DIR = BACKEND / "note_results"
KB_NOTES = Path(r"D:\development-projects\personal-projects\persional-knowledge\notes")
STATE = GOAL / "_kb_copy_state.json"
REPORT = GOAL / "_kb_copy_report.md"

# source label -> KB folder relative to notes/
TARGETS: dict[str, str] = {
    "前端小码哥": "technology/fullstack/frontend/前端小码哥",
    "大雨说Java": "technology/fullstack/backend/大雨说Java",
    "deepseekharness_": "technology/fullstack/AI/deepseekharness_",
    "炟烨 城市观察合集": "society/炟烨/城市观察合集",
    "我捞捞捞": "society/我捞捞捞",
    "喵类思维": "cognition/喵类思维",
    "小鱼爱配音x": "business/小鱼爱配音x",
    "高江子": "technology/computer/高江子",
    "程序员Web3社区": "technology/程序员Web3社区",
    "泽希讲求职": "interview/泽希讲求职",
    "ezindie小产品变现": "business/ezindie小产品变现",
    "熠辉IndieDev": "business/熠辉IndieDev",
    "温少创业记": "business/温少创业记",
    "渡一 前端提薪课精选合集": "technology/fullstack/frontend/渡一/17-提薪课精选",
    "瓜子项目社": "business/瓜子项目社",
    "与书籍度过漫长岁月": "cognition/与书籍度过漫长岁月",
    "思维实验室": "society/思维实验室",
    "dadafastrun": "business/dadafastrun",
    "你要相信光的呀哦": "business/你要相信光的呀哦",
    "bytezhou": "life/bytezhou",
    "小张阿姨的AI教学": "business/小张阿姨的AI教学",
    "PlanJ_": "society/PlanJ_",
    "老猫乔諵 我在B站做UP合集": "business/老猫乔諵",
    "AI深海圈": "business/AI深海圈",
}

# The six standalone videos are routed individually by BV id.
STANDALONE: dict[str, str] = {
    "BV1vK9eBREyD": "life/_散装视频",                     # 失业经历自述
    "BV1Hhpu6pEa1": "cognition/_散装视频",                # 极端提早退休
    "BV19rpE6iEpN": "technology/fullstack/AI/_散装视频",   # AI 科研长任务
    "BV1Zka56QEsv": "technology/fullstack/AI/_散装视频",   # Claude 账号/KYC 踩坑
    "BV154426xEha": "technology/fullstack/AI/_散装视频",   # AI 编程全流程
    "BV1Tit86MECG": "technology/llm/_散装视频",           # 音乐 GPT / 大模型本质
}

# Uploader name as recorded by yt-dlp -> source label used in TARGETS.
UPLOADER_TO_SOURCE = {label: label for label in TARGETS}

GENERIC_PARTS = re.compile(
    r"^(?:前言|导学|序|开篇|开场|课程介绍|课程说明|课程导论|简介|说明|介绍|引子|导读|总览)\s*[：:.]?\s*$"
)
PART_TITLE = re.compile(r"^(?P<video>.+?)\s+p(?P<page>\d+)\s+(?P<part>.+)$")

# Trailing rip tags on re-uploaded course parts: "…-1080P 高清-AVC", "… 4K".
QUALITY_TAG = re.compile(
    r"(?:[-_—\s]+(?:1080p|720p|480p|4k|8k|高清|超清|蓝光|avc|hevc|h\.?264|h\.?265)"
    r"(?:[-_—\s]+[^\s].*)?)$",
    re.IGNORECASE,
)


def strip_quality(name: str) -> str:
    out = name
    while True:
        new = QUALITY_TAG.sub("", out).strip(" -_—")
        if new == out or not new:
            return out
        out = new

_INVALID = {
    "/": "／", "\\": "＼", ":": "：", "*": "＊", "?": "？",
    '"': "＂", "<": "＜", ">": "＞", "|": "｜",
}


def sanitize(title: str, limit: int = 100) -> str:
    """Windows-safe filename (same rules as copy_programmer_fangge_notes.py)."""
    t = "".join(_INVALID.get(c, c) for c in title)
    t = "".join(c for c in t if c >= " " or c == "\t")
    t = re.sub(r"\s+", " ", t).strip().rstrip(". ")
    if len(t) > limit:
        t = t[:limit].rstrip(". ")
    return t or "untitled"


def video_id_of(url: str) -> str:
    m = re.search(r"(BV[0-9A-Za-z]{10})", url or "")
    if not m:
        return ""
    return f"{m.group(1)}_p{re.search(r'[?&]p=(\d+)', url).group(1)}" if re.search(r"[?&]p=(\d+)", url) else m.group(1)


def latest_successes() -> list[dict]:
    """One SUCCESS record per video_id, latest timestamp wins."""
    latest: dict[str, dict] = {}
    for line in PROGRESS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if rec.get("status") != "SUCCESS":
            continue
        vid = rec.get("video_id") or video_id_of(rec.get("url", ""))
        if not vid:
            continue
        known = latest.get(vid)
        if known is None or rec.get("ts", "") > known.get("ts", ""):
            latest[vid] = rec
    return sorted(latest.values(), key=lambda r: (r.get("source", ""), r.get("ts", "")))


def note_title(task_id: str) -> str | None:
    path = NOTE_DIR / f"{task_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None
    return ((data.get("audio_meta") or {}).get("title") or "").strip() or None


def filename_for(rec: dict) -> tuple[str, str]:
    """Returns (stem, part-tag) where the tag is '' or 'p<N>'."""
    raw = note_title(rec["task_id"]) or ""
    if not raw:
        return ("untitled", "")
    m = PART_TITLE.match(raw)
    if m:
        video, page, part = m.group("video").strip(), m.group("page"), m.group("part").strip()
        part = strip_quality(part)
        if GENERIC_PARTS.match(part):
            short = video[:20].rstrip(" -—_")
            return (sanitize(f"{short} - {part}"), f"p{page}")
        return (sanitize(part), f"p{page}")
    return (sanitize(strip_quality(raw)), "")


def orphan_records(known: list[dict]) -> list[dict]:
    """Notes whose markdown exists but never reached the progress log.

    The driver writes the progress line only when it observes SUCCESS; tasks that
    finished after the last poll, or during a kill, leave a finished note behind
    with no record. A task whose video already has a recorded SUCCESS is a stale
    earlier attempt and is skipped, not copied twice.
    """
    known_ids = {r["task_id"] for r in known}
    known_videos = {r.get("video_id") for r in known}
    out: list[dict] = []
    for md in NOTE_DIR.glob("*_markdown.md"):
        task_id = md.name[: -len("_markdown.md")]
        if task_id in known_ids:
            continue
        status = NOTE_DIR / f"{task_id}.status.json"
        if status.exists():
            try:
                if json.loads(status.read_text(encoding="utf-8", errors="replace")).get("status") != "SUCCESS":
                    continue
            except ValueError:
                # A few status files are plain-text write errors while .status.tmp
                # holds the real JSON; fall back to the markdown being present.
                tmp = NOTE_DIR / f"{task_id}.status.tmp"
                if tmp.exists():
                    try:
                        if json.loads(tmp.read_text(encoding="utf-8", errors="replace")).get("status") != "SUCCESS":
                            continue
                    except ValueError:
                        pass
        meta = NOTE_DIR / f"{task_id}.json"
        if not meta.exists():
            continue
        data = json.loads(meta.read_text(encoding="utf-8"))
        audio = data.get("audio_meta") or {}
        vid = audio.get("video_id") or ""
        if vid in known_videos:
            continue
        url = ((data.get("transcript") or {}).get("raw") or {}).get("bvid") or vid
        out.append({
            "source": UPLOADER_TO_SOURCE.get(
                ((data.get("audio_meta") or {}).get("raw_info") or {}).get("uploader", ""),
                "笔记待生成合集",
            ),
            "url": f"https://www.bilibili.com/video/{url}",
            "video_id": vid,
            "task_id": task_id,
            "ts": "",
            "orphan": True,
        })
    return out


def destination(rec: dict, state: dict) -> Path | None:
    """Folder this record belongs in (always a directory, never the file)."""
    vid = rec.get("video_id") or video_id_of(rec.get("url", ""))
    if vid in state:
        # Reuse the folder chosen on the previous run so re-runs are stable.
        return (KB_NOTES / state[vid]).parent
    bv = (re.search(r"(BV[0-9A-Za-z]{10})", rec.get("url", "")) or [None])
    bv = bv.group(1) if hasattr(bv, "group") else None
    if rec.get("source") == "笔记待生成合集" or not TARGETS.get(rec.get("source")):
        rel = STANDALONE.get(bv or "")
        return KB_NOTES / rel if rel else None
    return KB_NOTES / TARGETS[rec["source"]]


def unique_path(folder: Path, stem: str) -> Path:
    path = folder / f"{stem}.md"
    n = 2
    while path.exists():
        path = folder / f"{stem} ({n}).md"
        n += 1
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description="Copy v2 notes into the knowledge base")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="", help="only sources whose label contains this")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--include-orphans", action="store_true",
                    help="also copy notes that succeeded but were never written to the progress log")
    args = ap.parse_args()

    state = {}
    if STATE.exists():
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
        except ValueError:
            state = {}

    records = latest_successes()
    if args.include_orphans:
        records += orphan_records(records)
    if args.only:
        records = [r for r in records if args.only in r.get("source", "")]
    if args.limit:
        records = records[: args.limit]

    copied = skipped = missing = 0
    per_source = Counter()
    per_dest = Counter()
    anomalies: list[str] = []
    suffixes: list[str] = []
    unmapped: dict[str, int] = defaultdict(int)

    for rec in records:
        source = rec.get("source", "")
        md = NOTE_DIR / f"{rec['task_id']}_markdown.md"
        if not md.exists():
            missing += 1
            anomalies.append(f"missing markdown: {rec['task_id']} ({source})")
            continue
        folder = destination(rec, state)
        if folder is None:
            unmapped[source] += 1
            continue
        stem, _ = filename_for(rec)
        text = md.read_text(encoding="utf-8", errors="replace")
        if "你好，我无法给到相关内容" in text[:400]:
            anomalies.append(f"refusal content: {source} / {stem}")

        vid = rec.get("video_id") or video_id_of(rec.get("url", ""))
        recorded = KB_NOTES / state[vid] if vid in state else None
        if recorded is not None:
            if recorded.exists() and recorded.read_bytes() == md.read_bytes():
                skipped += 1
                continue
            folder = recorded.parent

        existing = folder / f"{stem}.md"
        if existing.exists():
            if existing.read_bytes() == md.read_bytes():
                skipped += 1
                per_source[source] += 0
                continue
            suffixes.append(f"{source} / {stem}")

        target = existing if not existing.exists() else unique_path(folder, stem)
        if not args.dry_run:
            folder.mkdir(parents=True, exist_ok=True)
            shutil.copy2(md, target)
            state[rec.get("video_id") or video_id_of(rec.get("url", ""))] = str(target.relative_to(KB_NOTES))
        copied += 1
        per_source[source] += 1
        per_dest[folder.relative_to(KB_NOTES).as_posix()] += 1

    if not args.dry_run:
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = [
        "# KB copy report",
        "",
        f"- mode: {'dry-run' if args.dry_run else 'copy'}",
        f"- records: {len(records)}",
        f"- copied: {copied}  skipped (identical): {skipped}  missing source: {missing}",
        "",
        "## per source",
        "| source | copied |",
        "|---|---:|",
    ]
    for source, n in sorted(per_source.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {source} | {n} |")
    lines += ["", "## per destination", "| folder | notes |", "|---|---:|"]
    for folder, n in sorted(per_dest.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"| {folder} | {n} |")
    if suffixes:
        lines += ["", f"## title collisions (suffixed) — {len(suffixes)}", ""]
        lines += [f"- {s}" for s in suffixes[:200]]
    if umapped := dict(unmapped):
        lines += ["", "## unmapped sources", ""] + [f"- {k}: {v}" for k, v in umapped.items()]
    if anomalies:
        lines += ["", f"## anomalies — {len(anomalies)}", ""] + [f"- {a}" for a in anomalies[:200]]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"records={len(records)} copied={copied} skipped={skipped} "
          f"missing={missing} unmapped={sum(unmapped.values())} "
          f"collisions={len(suffixes)} anomalies={len(anomalies)}")
    print(f"report: {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
