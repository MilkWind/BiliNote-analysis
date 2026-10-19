#!/usr/bin/env python3
"""Fetch every 分P (page) title for a list of Bilibili videos.

Input is a text file with one video URL or bare ``BV...`` id per line — the
format produced by ``fetch_space_videos.py``. For each video we call
``x/web-interface/view``, which returns both the video title and its ``pages``
array (``page`` / ``part`` / ``cid`` / ``duration``), so a single request per
video is enough.

Outputs (all optional, UTF-8):

- ``--json``  structured ``{bvid: {title, pubdate, pages: [...]}}``
- ``--md``    human-readable Markdown, one section per video
- ``--uniq``  deduplicated 分P titles, in first-seen order

The dedup step is what makes repeated 分P across re-uploaded/collection videos
collapse into one line. Matching is exact after trimming surrounding whitespace.

Usage (run from the ``backend/`` directory so the venv is used):

    python script/pagination_query/fetch_video_pages.py ../goal_videos/temp_bv_2026.txt \
        --json ../goal_videos/temp_pages_2026.json \
        --md ../goal_videos/temp_pages_2026.md \
        --uniq ../goal_videos/temp_parts_unique_2026.txt
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

API = "https://api.bilibili.com/x/web-interface/view"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com/",
}


def _load_cookie_from_config() -> str | None:
    """Best-effort read of the bilibili cookie from ``config/downloader.json``."""
    candidates = [
        Path("config/downloader.json"),
        Path("backend/config/downloader.json"),
        Path(__file__).resolve().parents[2] / "config" / "downloader.json",
    ]
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cookie = data.get("bilibili", {}).get("cookie")
            if cookie:
                return cookie
        except (OSError, ValueError):
            continue
    return None


def _parse_bvid(line: str) -> str | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    m = re.search(r"(BV[0-9A-Za-z]{10})", line)
    return m.group(1) if m else None


def read_bvids(path: Path) -> list[str]:
    bvids: list[str] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        bvid = _parse_bvid(line)
        if bvid and bvid not in seen:
            seen.add(bvid)
            bvids.append(bvid)
    return bvids


def _session(cookie: str | None) -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    if cookie:
        s.headers["Cookie"] = cookie
    return s


def fetch_video(session: requests.Session, bvid: str, retries: int, sleep: float) -> dict:
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            r = session.get(API, params={"bvid": bvid}, timeout=20)
            r.raise_for_status()
            data = r.json()
            if data.get("code") != 0:
                raise RuntimeError(f"code={data.get('code')} message={data.get('message')}")
            d = data["data"]
            return {
                "bvid": bvid,
                "aid": d.get("aid"),
                "title": d.get("title", ""),
                "pubdate": d.get("pubdate", 0),
                "videos": d.get("videos", len(d.get("pages") or [])),
                "pages": [
                    {
                        "page": p.get("page"),
                        "part": p.get("part", ""),
                        "cid": p.get("cid"),
                        "duration": p.get("duration"),
                    }
                    for p in (d.get("pages") or [])
                ],
            }
        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < retries:
                wait = 3 * attempt
                print(f"{bvid} 第 {attempt} 次失败（{e}），{wait}s 后重试…", file=sys.stderr)
                time.sleep(wait)
    raise SystemExit(f"{bvid} 获取失败：{last_err}")


# Leading numbering forms that differ between otherwise identical 分P:
#   【1】xxx / 第1集：xxx / P1 xxx / 1.xxx / 01-xxx / (1) xxx
_PREFIX_PATTERNS = (
    re.compile(r"^[【\[\(（]\s*\d+\s*[】\]\)）]\s*"),
    re.compile(r"^第\s*\d+\s*[讲节课集篇]\s*[:：.、\-]?\s*"),
    re.compile(r"^[Pp]\s*\d+\s*[:：.、\-]?\s*"),
    re.compile(r"^\d+\s*[-_.、:：]\s*"),
)


def strip_title_prefixes(title: str) -> str:
    """Drop repeated leading numbering and collapse whitespace (display form)."""
    key = title.strip()
    changed = True
    while changed:
        changed = False
        for pattern in _PREFIX_PATTERNS:
            new_key = pattern.sub("", key, count=1)
            if new_key != key:
                key = new_key
                changed = True
    return re.sub(r"\s+", " ", key).strip()


def normalize_title(title: str) -> str:
    """Dedup key: prefix-free and whitespace-insensitive."""
    return re.sub(r"\s+", "", strip_title_prefixes(title))


def dedupe_titles(videos: list[dict], normalize: bool = True) -> list[str]:
    """Unique 分P titles in first-seen order (videos are newest-first).

    With ``normalize=True`` titles that only differ by a leading index (or
    whitespace) collapse into one; the returned title is the first-seen title
    with its numbering prefixes removed.
    """
    seen: set[str] = set()
    unique: list[str] = []
    for v in videos:
        for p in v["pages"]:
            title = (p.get("part") or "").strip()
            if normalize:
                display = strip_title_prefixes(title)
                key = re.sub(r"\s+", "", display)
            else:
                display = key = title
            if key and key not in seen:
                seen.add(key)
                unique.append(display)
    return unique


def render_markdown(videos: list[dict], unique: list[str], unique_exact: list[str]) -> str:
    total_pages = sum(len(v["pages"]) for v in videos)
    lines = [
        "# 程序员方格 2026 年投稿与分P",
        "",
        f"- 视频数：{len(videos)}",
        f"- 分P 总数（含重复）：{total_pages}",
        f"- 去重后（标题完全一致）：{len(unique_exact)}",
        f"- 归一化去重后（忽略开头序号/空白）：{len(unique)}",
        "",
    ]
    for v in videos:
        lines.append(f"## {v['title']}")
        lines.append("")
        lines.append(f"- BV：https://www.bilibili.com/video/{v['bvid']}")
        lines.append(f"- 分P 数：{len(v['pages'])}")
        lines.append("")
        for p in v["pages"]:
            lines.append(f"{p['page']}. {p['part']}")
        lines.append("")
    lines.append("## 归一化去重后的分P 标题（已去除开头序号）")
    lines.append("")
    for i, title in enumerate(unique, 1):
        lines.append(f"{i}. {title}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="拉取 B 站视频的分P 列表并去重标题")
    parser.add_argument("input", nargs="?", help="视频 URL / BV 号列表文件")
    parser.add_argument("--from-json", help="复用已抓取的 JSON，不再请求接口")
    parser.add_argument("--json", help="结构化结果输出路径")
    parser.add_argument("--md", help="Markdown 报告输出路径")
    parser.add_argument("--uniq", help="归一化去重后的分P 标题输出路径")
    parser.add_argument("--uniq-exact", help="仅按标题完全一致去重后的输出路径")
    parser.add_argument("--cookie", help="B 站 cookie 字符串；缺省时从 config/downloader.json 读取")
    parser.add_argument("--sleep", type=float, default=1.5, help="请求间隔秒数，默认 1.5")
    parser.add_argument("--retries", type=int, default=3, help="单个视频失败重试次数，默认 3")
    args = parser.parse_args()

    if args.from_json:
        videos = json.loads(Path(args.from_json).read_text(encoding="utf-8"))
    else:
        if not args.input:
            parser.error("需要提供输入文件，或使用 --from-json 复用已有数据")
        bvids = read_bvids(Path(args.input))
        if not bvids:
            raise SystemExit(f"未从 {args.input} 解析出任何 BV 号")

        session = _session(args.cookie or _load_cookie_from_config())
        videos = []
        for i, bvid in enumerate(bvids, 1):
            video = fetch_video(session, bvid, args.retries, args.sleep)
            videos.append(video)
            print(f"[{i}/{len(bvids)}] {bvid} {video['title']} ({len(video['pages'])}P)", file=sys.stderr)
            if i < len(bvids):
                time.sleep(args.sleep)

    unique = dedupe_titles(videos)
    unique_exact = dedupe_titles(videos, normalize=False)
    total_pages = sum(len(v["pages"]) for v in videos)

    if args.json:
        Path(args.json).write_text(
            json.dumps(videos, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    if args.md:
        Path(args.md).write_text(
            render_markdown(videos, unique, unique_exact), encoding="utf-8"
        )
    if args.uniq:
        Path(args.uniq).write_text("\n".join(unique) + ("\n" if unique else ""), encoding="utf-8")
    if args.uniq_exact:
        Path(args.uniq_exact).write_text(
            "\n".join(unique_exact) + ("\n" if unique_exact else ""), encoding="utf-8"
        )

    print(
        f"视频 {len(videos)} 个，分P {total_pages} 条，"
        f"完全一致去重 {len(unique_exact)} 条，归一化去重 {len(unique)} 条",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
