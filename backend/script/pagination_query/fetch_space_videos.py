#!/usr/bin/env python3
"""Fetch every video URL from a Bilibili user's space.

This wraps yt-dlp's ``BilibiliSpaceVideoIE``, which handles the painful part
for us: it paginates ``x/space/wbi/arc/search``, re-computes the WBI signature
(``w_rid``) and timestamp (``wts``) for *every* page, and injects the
``dm_img_*`` / ``web_location`` browser-fingerprint params that Bilibili's risk
control requires. Manually editing a single ``pn=`` on a captured URL will fail
precisely because ``w_rid`` is an MD5 over the whole query string — see
``api-analysis/bilibili/`` for the raw capture.

One catch: upstream yt-dlp sends an *empty* ``dm_img_list=[]`` and random-garbage
``dm_img_str``, which Bilibili's risk control rejects (HTTP 412). A real browser
sends a non-empty mouse-trajectory list and constant WebGL/GPU strings. We
monkey-patch ``_sign_wbi`` to inject realistic fingerprint data before signing.

Usage (run from the ``backend/`` directory so the venv is used):

    python script/bilibili/fetch_space_videos.py https://space.bilibili.com/3494367333452734/video -o goal_videos/douyi.txt
    python script/bilibili/fetch_space_videos.py 3494367333452734 --cookie "SESSDATA=...; bili_jct=..." -o out.txt
    python script/bilibili/fetch_space_videos.py 3494367333452734 --bvid          # print bare BV ids

Output is one ``https://www.bilibili.com/video/BV...`` per line (matches the
format of the files under ``goal_videos/``).
"""
from __future__ import annotations

import argparse
import base64
import json
import random
import re
import sys
import tempfile
import time
from pathlib import Path

import yt_dlp


# ---------------------------------------------------------------------------
# Realistic browser-fingerprint generation + WBI-signing patch
# ---------------------------------------------------------------------------

_WEBGL = "WebGL 1.0 (OpenGL ES 2.0 Chromium)"
_GPU = "ANGLE (Intel, Intel(R) Arc(TM) Graphics (0x00007D55) Direct3D11 vs_5_0 ps_5_0, D3D11)Google Inc. (Intel)"
_ELEM = "vui_button vui_button--active vui_button--active-blue vui_button--no-transition vui_pagenation--btn vui_pagenation--btn-n"


def _b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


def _realistic_dm_img_list() -> str:
    """Non-empty mouse-trajectory array, mirroring the shape in api-analysis."""
    pts = []
    x, y = random.randint(2000, 3500), random.randint(-1800, 1500)
    ts = random.randint(800_000, 1_000_000)
    for _ in range(random.randint(40, 60)):
        x += random.randint(-300, 300)
        y += random.randint(-300, 300)
        ts += random.randint(80, 200)
        pts.append({
            "x": x, "y": y, "z": random.randint(0, 3000),
            "timestamp": ts, "k": random.randint(60, 126),
            "type": random.choice([0, 0, 0, 0, 1]),
        })
    return json.dumps(pts, separators=(",", ":"))


def _realistic_dm_img_inter() -> str:
    ds = [{
        "t": random.randint(5, 10),
        "c": _b64(_ELEM),
        "p": [random.randint(3000, 7000), random.randint(0, 200), random.randint(5000, 10_000)],
        "s": [random.randint(200, 500), random.randint(300, 600), random.randint(400, 800)],
    }]
    return json.dumps({
        "ds": ds,
        "wh": [random.randint(3000, 4000), random.randint(3000, 4000), random.randint(30, 100)],
        "of": [random.randint(4000, 8000), random.randint(4000, 8000), random.randint(150, 400)],
    }, separators=(",", ":"))


def _patch_space_fingerprint() -> None:
    """Replace yt-dlp's empty/random dm_img_* with realistic values before WBI signing."""
    from yt_dlp.extractor.bilibili import BilibiliBaseIE

    original = BilibiliBaseIE._sign_wbi
    if getattr(original, "_bili_space_patched", False):
        return

    def _patched(self, params, video_id):
        if "dm_img_list" in params:
            params["dm_img_list"] = _realistic_dm_img_list()
            params["dm_img_inter"] = _realistic_dm_img_inter()
            params["dm_img_str"] = _b64(_WEBGL)
            params["dm_cover_img_str"] = _b64(_GPU)
        return original(self, params, video_id)

    _patched._bili_space_patched = True
    BilibiliBaseIE._sign_wbi = _patched


# ---------------------------------------------------------------------------
# Cookie handling (mirrors BilibiliDownloader._write_netscape_cookie_file)
# ---------------------------------------------------------------------------

def _write_netscape_cookie_file(cookie: str) -> str:
    """Write a raw ``k=v; k=v`` cookie string to a Netscape cookiefile."""
    lines = ["# Netscape HTTP Cookie File\n"]
    for pair in cookie.split("; "):
        if "=" in pair:
            key, value = pair.split("=", 1)
            lines.append(f".bilibili.com\tTRUE\t/\tFALSE\t0\t{key}\t{value}\n")
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    tmp.writelines(lines)
    tmp.close()
    return tmp.name


def _load_cookie_from_config() -> str | None:
    """Best-effort read of the bilibili cookie from ``fetch_config.json``."""
    candidates = [
        Path(__file__).parent / "fetch_config.json",
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


def resolve_space_url(target: str) -> str:
    """Accept a bare mid or a full space URL, return a canonical space URL."""
    target = target.strip()
    if target.isdigit():
        mid = target
    else:
        m = re.search(r"space\.bilibili\.com/(\d+)", target)
        if not m:
            raise SystemExit(f"无法从 '{target}' 解析出 mid，请输入空间链接或纯数字 mid")
        mid = m.group(1)
    return f"https://space.bilibili.com/{mid}/video"


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def _build_opts(cookie: str | None, cookiefile: str | None, sleep: float, limit: int) -> dict:
    opts: dict = {
        "extract_flat": "in_playlist",
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": False,
        "ignoreerrors": True,
        "sleep_interval_requests": sleep,
    }
    if cookiefile:
        opts["cookiefile"] = cookiefile
    elif cookie:
        opts["cookiefile"] = _write_netscape_cookie_file(cookie)
    if limit:
        opts["playlistend"] = limit
    return opts


def fetch_video_urls(
    space_url: str,
    order: str,
    cookie: str | None,
    cookiefile: str | None,
    sleep: float,
    limit: int,
    retries: int,
) -> list[str]:
    """Return the list of full video URLs in the user's space."""
    if order:
        sep = "&" if "?" in space_url else "?"
        space_url = f"{space_url}{sep}order={order}"

    urls: list[str] = []
    for attempt in range(1, retries + 1):
        with yt_dlp.YoutubeDL(_build_opts(cookie, cookiefile, sleep, limit)) as ydl:
            info = ydl.extract_info(space_url, download=False)
            if info:
                urls = [
                    f"https://www.bilibili.com/video/{e['id']}"
                    for e in info.get("entries") or []
                    if e and e.get("id")
                ]
        if urls:
            return urls
        if attempt < retries:
            wait = 5 * attempt
            print(f"第 {attempt} 次未取到数据（412 风控），{wait}s 后重试…", file=sys.stderr)
            time.sleep(wait)

    raise SystemExit(
        "未获取到任何视频。可能原因：cookie 缺失/失效、被风控(-352/-412)拦截，或该空间无投稿。"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="拉取 B 站 UP 主空间全部投稿视频 URL")
    parser.add_argument("target", help="空间链接（https://space.bilibili.com/<mid>/video）或纯数字 mid")
    parser.add_argument("-o", "--output", help="输出文件路径；缺省则打印到标准输出")
    parser.add_argument("--cookie", help="B 站 cookie 字符串（k=v; k=v）；缺省时尝试从 ./script/bilibili/fetch_config.json 读取")
    parser.add_argument("--cookie-file", help="Netscape 格式 cookie 文件路径（优先级最高）")
    parser.add_argument("--order", default="pubdate", help="排序方式，默认 pubdate")
    parser.add_argument("--sleep", type=float, default=5.0, help="每次请求间隔秒数，默认 5.0（防 412 限流）")
    parser.add_argument("--retries", type=int, default=3, help="整次拉取失败时的重试次数，默认 3")
    parser.add_argument("--bvid", action="store_true", help="仅输出 BV 号（不含域名前缀）")
    parser.add_argument("--limit", type=int, default=0, help="最多输出 N 条（0 表示全部）")
    args = parser.parse_args()

    _patch_space_fingerprint()

    space_url = resolve_space_url(args.target)
    cookie = args.cookie or _load_cookie_from_config()
    if cookie and "=" not in cookie:
        # Bare SESSDATA value (no key) -> turn it into a valid cookie.
        cookie = f"SESSDATA={cookie}"

    urls = fetch_video_urls(space_url, args.order, cookie, args.cookie_file, args.sleep, args.limit, args.retries)

    lines = [u.rsplit("/", 1)[-1] for u in urls] if args.bvid else urls
    text = "\n".join(lines) + ("\n" if lines else "")

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"已写入 {len(lines)} 条到 {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
