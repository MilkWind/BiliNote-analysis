#!/usr/bin/env python3
"""Attach source link + title header to each note, copy to duyi, rename by title.

Dedups retry artifacts (same video_id, multiple task_ids) keeping the longest
note. Does not overwrite files that already exist in the destination.
"""
import json
from pathlib import Path
from collections import defaultdict

SRC = Path("note_results")
DST = Path(r"D:/development-projects/document-projects/persional-knowledge/technology/frontend/duyi")
LINK_PREFIX = "> 来源链接："

CHANNEL_SUFFIX = "【渡一教育】"
FULLWIDTH = str.maketrans({
    "\\": "＼", "/": "／", ":": "：", "*": "＊", "?": "？",
    '"': "＂", "<": "＜", ">": "＞", "|": "｜",
})


def sanitize_filename(title: str, vid: str) -> str:
    t = title.replace(CHANNEL_SUFFIX, "")
    t = t.strip()
    while t and t[-1] in "?？":
        t = t[:-1]
    t = t.strip()
    t = t.translate(FULLWIDTH)
    t = "".join(c for c in t if ord(c) >= 32)
    t = t.strip().rstrip(". ")
    if not t:
        t = vid
    if len(t) > 180:
        t = t[:180]
    return t + ".md"


def main():
    jsons = sorted(p for p in SRC.glob("*.json")
                   if not any(k in p.name for k in ("status", "audio", "transcript")))

    # group by video_id -> list of (task_id, markdown_len, title)
    by_vid = defaultdict(list)
    for jp in jsons:
        d = json.loads(jp.read_text(encoding="utf-8"))
        am = d.get("audio_meta") or {}
        vid = (am.get("video_id") or "").strip()
        title = (am.get("title") or "").strip()
        md = SRC / f"{jp.stem}_markdown.md"
        body = md.read_text(encoding="utf-8") if md.exists() else ""
        by_vid[vid].append((jp.stem, len(body), title, body))

    kept = {}
    for vid, entries in by_vid.items():
        tid, length, title, body = max(entries, key=lambda e: e[1])  # longest
        kept[vid] = (tid, title, body)

    used_names = {}
    written = skipped = collisions = 0
    report = []

    for vid in sorted(kept):
        tid, title, body = kept[vid]
        url = f"https://www.bilibili.com/video/{vid}"

        # strip any existing link line / title header from body
        lines = body.strip("\n").splitlines()
        while lines and (not lines[0].strip() or lines[0].strip().startswith(LINK_PREFIX)
                         or lines[0].lstrip().startswith("# ")):
            lines = lines[1:]
        clean_body = "\n".join(lines).strip("\n")

        full = f"# {title} 笔记整理\n\n{LINK_PREFIX}{url}\n\n{clean_body}\n"

        fname = sanitize_filename(title, vid)
        if fname in used_names and used_names[fname] != vid:
            stem = fname[:-3]
            fname = f"{stem} {vid}.md"
            collisions += 1
        used_names[fname] = vid

        dst = DST / fname
        if dst.exists():
            skipped += 1
            report.append(f"SKIP(exists) {fname}")
            continue
        dst.write_text(full, encoding="utf-8")
        written += 1

        # attach link to the source note in note_results (idempotent)
        src_md = SRC / f"{tid}_markdown.md"
        if src_md.exists():
            cur = src_md.read_text(encoding="utf-8")
            if not cur.lstrip().startswith(LINK_PREFIX):
                src_md.write_text(f"{LINK_PREFIX}{url}\n\n{cur}", encoding="utf-8")

    report.append("")
    report.append(f"total distinct videos: {len(kept)}")
    report.append(f"written: {written}")
    report.append(f"skipped (already exists): {skipped}")
    report.append(f"filename collisions resolved with BV suffix: {collisions}")
    if len(kept) != len(jsons):
        report.append(f"retry-duplicate notes dropped: {len(jsons) - len(kept)}")

    Path("copy_report.txt").write_text("\n".join(report), encoding="utf-8")
    print(f"done: distinct={len(kept)} written={written} skipped={skipped} collisions={collisions}")


if __name__ == "__main__":
    main()
