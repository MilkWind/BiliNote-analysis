#!/usr/bin/env python3
"""Build the per-source Bilibili URL list files referenced by goal_videos/temp.txt.

For every source line in temp.txt this script writes ``goal_videos/<label>.txt``
with one video URL per line (same format as the existing goal_videos lists and
the format ``batch_goal_notes.py`` consumes).

Source kinds
------------
* ``space``  -- every upload of a UP 主, paginated through
  ``x/space/wbi/arc/search`` (WBI re-signed per page, realistic dm_img_* patched
  by ``fetch_space_videos.py``).
* ``list``   -- one 合集/season, paginated through
  ``x/polymer/web-space/seasons_archives_list``.

Per-source rules from temp.txt
------------------------------
* 思维实验室          -> only videos published on/after 2025-01-01 (Beijing).
* 我捞捞捞            -> only 2026 videos, excluding 小说/影视类 videos.
* deepseekharness_    -> expand every video into its 分P, dedupe 分P titles,
                         then drop parts whose title is near-identical to a note
                         title already present in persional-knowledge.
* 渡一 前端提薪课精选合集 -> same 分P + knowledge-base dedupe ("老规矩").
* 程序员方格          -> videos since 2026-10-20 (inclusive), expanded into
                         分P and deduped against the existing 程序员方格 notes.

Dedup details
-------------
分P titles are deduped after stripping leading 【1】 / 第1集 / P1 / 01- numbering,
trailing rip tags such as ``-1080P 高清-AVC``, and whitespace.

Knowledge-base matching compares normalised titles (numbering and punctuation
removed, case-folded) and flags a duplicate when a note title is identical, is
contained in the part title (or vice versa) with >= 80% length overlap, or has
a SequenceMatcher ratio >= 0.88. A note source link with the same (BV, page) is
an exact duplicate. Dropped items, near-misses that were kept, and the full kept
list are written to ``goal_videos/_dedupe_reports/`` for review.

Usage (run with the backend venv):
    python script/pagination_query/build_goal_video_lists.py --fetch-only
    python script/pagination_query/build_goal_video_lists.py --only deepseek
    python script/pagination_query/build_goal_video_lists.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Callable

import requests
import yt_dlp
from yt_dlp.extractor.bilibili import BilibiliSpaceVideoIE

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND = SCRIPT_DIR.parents[1]
ROOT = BACKEND.parent
GOAL = ROOT / "goal_videos"
CONFIG = BACKEND / "config" / "downloader.json"
CACHE = Path(tempfile.gettempdir()) / "bili_goal_lists_cache"
REPORT_DIR = GOAL / "_dedupe_reports"
KB_ROOT = Path(r"D:\development-projects\personal-projects\persional-knowledge")

sys.path.insert(0, str(SCRIPT_DIR))
from fetch_space_videos import _build_opts, _patch_space_fingerprint  # noqa: E402
from fetch_video_pages import strip_title_prefixes  # noqa: E402

SLEEP_PAGE = 4.0       # seconds between space/list pages
SLEEP_VIEW = 1.3       # seconds between x/web-interface/view calls
RETRIES = 4

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

BEIJING = timezone(timedelta(hours=8))


# ---------------------------------------------------------------------------
# Source definitions (one per line of goal_videos/temp.txt)
# ---------------------------------------------------------------------------

SOURCES: list[dict] = [
    {"label": "bytezhou", "kind": "space", "mid": "28745756"},
    {"label": "dadafastrun", "kind": "space", "mid": "443251021"},
    {"label": "deepseekharness_", "kind": "space", "mid": "620834560",
     "parts": True, "kb_dedupe": True},
    {"label": "渡一 前端提薪课精选合集", "kind": "list", "mid": "666759136", "sid": "8483659",
     "parts": True, "kb_dedupe": True},
    {"label": "小张阿姨的AI教学", "kind": "space", "mid": "348543296"},
    {"label": "泽希讲求职", "kind": "space", "mid": "3546692477520851"},
    {"label": "ezindie小产品变现", "kind": "space", "mid": "395127673"},
    {"label": "炟烨 城市观察合集", "kind": "list", "mid": "2017204408", "sid": "8582873"},
    {"label": "瓜子项目社", "kind": "space", "mid": "3546785467337088"},
    {"label": "温少创业记", "kind": "space", "mid": "3546970553584384"},
    {"label": "喵类思维", "kind": "space", "mid": "1092054950"},
    {"label": "思维实验室", "kind": "space", "mid": "14583962", "since": "2025-01-01"},
    {"label": "你要相信光的呀哦", "kind": "space", "mid": "3546927803140311"},
    {"label": "小鱼爱配音x", "kind": "space", "mid": "194021667"},
    {"label": "AI深海圈", "kind": "space", "mid": "3690998536341747"},
    {"label": "我捞捞捞", "kind": "space", "mid": "693612555", "since": "2026-01-01",
     "exclude_label": "exclude 小说/影视类",
     # 网文/小说评级、书单、小说剧情讲解 + 影视/动画/剪辑类，均不属于要解析的知识类视频。
     # 书名号标题默认视为小说/影视内容，仅放行历史典籍类。
     "exclude": (
         r"小说|网文|书荒|书单|评级|锐评|封神|盘点|修仙|仙侠|玄幻|都市文|历史文|"
         r"末世|种田|无限流|后宫|斗罗|同人|穿越|重生|系统流|爽文|文抄公|完结|连载|"
         r"起点|番茄|讲了个什么故事|书评|读书|看书|作者|合订本|"
         r"电影|电视剧|影视|动画|动漫|番剧|短剧|纪录片|解说|剧情|剪辑|混剪|"
         r"角色|演员|导演|票房|预告|番外|谍战剧|编剧|"
         r"超人|漫威|奥特曼|复仇者|流浪地球|变种人|超级英雄|"
         r"《(?!\s*(?:孙子兵法|中俄尼布楚条约|史记|资治通鉴|三国志|汉书|后汉书|"
         r"论语|道德经|韩非子|商君书|天工开物|本草纲目|梦溪笔谈|永乐大典|"
         r"徐霞客游记|毛泽东选集|资本论)\s*》)[^》]*》"
     )},
    {"label": "程序员Web3社区", "kind": "space", "mid": "3546883165259823"},
    {"label": "大雨说Java", "kind": "space", "mid": "3546669039749947"},
    {"label": "与书籍度过漫长岁月", "kind": "space", "mid": "252099076"},
    {"label": "老猫乔諵 我在B站做UP合集", "kind": "list", "mid": "1007603480", "sid": "6683044"},
    {"label": "前端小码哥", "kind": "space", "mid": "3546719360911487"},
    {"label": "高江子", "kind": "space", "mid": "11294180"},
    {"label": "熠辉IndieDev", "kind": "space", "mid": "39930228"},
    {"label": "PlanJ_", "kind": "space", "mid": "3546982400396253"},
    {"label": "程序员方格", "kind": "space", "mid": "3546980777199728",
     "since": "2026-10-20", "parts": True, "kb_dedupe": True},
]

PENDING_BVS = [
    "BV1vK9eBREyD", "BV1Hhpu6pEa1", "BV19rpE6iEpN",
    "BV1Zka56QEsv", "BV154426xEha", "BV1Tit86MECG",
]
PENDING_LABEL = "笔记待生成合集"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def load_cookie() -> str | None:
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8")).get("bilibili", {}).get("cookie")
    except (OSError, ValueError):
        return None


def _session(cookie: str | None) -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Referer": "https://www.bilibili.com/"})
    if cookie:
        s.headers["Cookie"] = cookie
    return s


def _retry(fn: Callable, what: str):
    last: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last = e
            wait = 10 * attempt
            log(f"[retry {attempt}/{RETRIES}] {what}: {e}; sleeping {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"{what} failed after {RETRIES} attempts: {last}")


def _parse_since(value: str) -> int:
    return int(datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=BEIJING).timestamp())


def _cache_path(name: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    return CACHE / name


def _load_cache(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            return None
    return None


def _save_cache(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def fetch_space(mid: str, cookie: str | None, refresh: bool = False) -> list[dict]:
    cache = _cache_path(f"space_{mid}.json")
    cached = None if refresh else _load_cache(cache)
    if cached is not None:
        return cached

    _patch_space_fingerprint()
    rows: list[dict] = []
    seen: set[str] = set()

    with yt_dlp.YoutubeDL(_build_opts(cookie, None, 0, 0)) as ydl:
        ie = BilibiliSpaceVideoIE(ydl)
        page = 1
        while True:
            def get_page(pn: int = page):
                params = ie._sign_wbi({
                    "mid": mid, "ps": 30, "pn": pn, "order": "pubdate",
                    "platform": "web", "web_location": 1550101,
                }, None)
                return ie._download_json(
                    "https://api.bilibili.com/x/space/wbi/arc/search", mid,
                    query=params,
                    headers={"Referer": f"https://space.bilibili.com/{mid}/video"},
                )

            data = _retry(get_page, f"space {mid} page {page}")
            d = data.get("data") or {}
            vlist = ((d.get("list") or {}).get("vlist")) or []
            if not vlist:
                break
            for v in vlist:
                bvid = v.get("bvid")
                if not bvid or bvid in seen:
                    continue
                seen.add(bvid)
                rows.append({
                    "bvid": bvid,
                    "title": v.get("title") or "",
                    "created": int(v.get("created") or 0),
                    "typeid": v.get("typeid"),
                    "length": v.get("length") or "",
                })
            total = int((d.get("page") or {}).get("count") or 0)
            log(f"[space {mid}] page {page}: +{len(vlist)} (total {len(rows)}/{total})")
            if total and len(rows) >= total:
                break
            page += 1
            time.sleep(SLEEP_PAGE)

    _save_cache(cache, rows)
    return rows


def fetch_list(mid: str, sid: str, cookie: str | None, refresh: bool = False) -> list[dict]:
    cache = _cache_path(f"list_{mid}_{sid}.json")
    cached = None if refresh else _load_cache(cache)
    if cached is not None:
        return cached

    session = _session(cookie)
    url = "https://api.bilibili.com/x/polymer/web-space/seasons_archives_list"
    referer = f"https://space.bilibili.com/{mid}/lists/{sid}"
    rows: list[dict] = []
    seen: set[str] = set()
    page = 1
    total = None

    while True:
        def get_page(pn: int = page):
            r = session.get(url, params={
                "mid": mid, "season_id": sid, "page_num": pn, "page_size": 30,
            }, headers={"Referer": referer}, timeout=20)
            r.raise_for_status()
            js = r.json()
            if js.get("code") != 0:
                raise RuntimeError(f"code={js.get('code')} msg={js.get('message')}")
            return js.get("data") or {}

        d = _retry(get_page, f"list {mid}/{sid} page {page}")
        archives = d.get("archives") or []
        if not archives:
            break
        total = int((d.get("page") or {}).get("total") or 0)
        for a in archives:
            bvid = a.get("bvid")
            if not bvid or bvid in seen:
                continue
            seen.add(bvid)
            rows.append({
                "bvid": bvid,
                "title": a.get("title") or "",
                "created": int(a.get("pubdate") or a.get("ctime") or 0),
                "typeid": None,
                "length": str(a.get("duration") or ""),
            })
        log(f"[list {mid}/{sid}] page {page}: +{len(archives)} (total {len(rows)}/{total})")
        if total and len(rows) >= total:
            break
        page += 1
        time.sleep(SLEEP_PAGE)

    _save_cache(cache, rows)
    return rows


def fetch_views(label: str, bvids: list[str], cookie: str | None,
                refresh: bool = False) -> dict[str, dict]:
    """Fetch title + pages for every BV; cached incrementally for resume."""
    cache = _cache_path(f"views_{_safe_name(label)}.json")
    data: dict[str, dict] = {} if refresh else (_load_cache(cache) or {})
    session = _session(cookie)
    todo = [b for b in bvids if b not in data]
    log(f"[views {label}] {len(bvids)} total, {len(todo)} to fetch")
    for i, bv in enumerate(todo, 1):
        def get_one(bvid: str = bv):
            r = session.get("https://api.bilibili.com/x/web-interface/view",
                            params={"bvid": bvid}, timeout=20)
            r.raise_for_status()
            js = r.json()
            if js.get("code") != 0:
                raise RuntimeError(f"{bvid}: code={js.get('code')} msg={js.get('message')}")
            d = js["data"]
            return {
                "bvid": bvid,
                "title": d.get("title") or "",
                "pubdate": int(d.get("pubdate") or 0),
                "pages": [
                    {"page": p.get("page"), "part": p.get("part") or "",
                     "duration": p.get("duration")}
                    for p in (d.get("pages") or [])
                ],
            }

        try:
            data[bv] = _retry(get_one, f"view {bv}")
        except RuntimeError as e:
            log(f"[views {label}] WARN {e}; treating as single-part with empty title")
            data[bv] = {"bvid": bv, "title": "", "pubdate": 0, "pages": []}
        if i % 10 == 0 or i == len(todo):
            _save_cache(cache, data)
        if i < len(todo):
            time.sleep(SLEEP_VIEW)
    _save_cache(cache, data)
    return data


def _safe_name(label: str) -> str:
    return re.sub(r'[\\/:*?"<>|\s]+', "_", label)


# ---------------------------------------------------------------------------
# Knowledge-base title matching
# ---------------------------------------------------------------------------

_NOISE = re.compile(
    r"(?:[-_—|｜·]\s*)?(?:科教|公开课|完整版|渡一教育|渡一|官方|高清|1080P|4K)\s*$",
    re.IGNORECASE,
)

# Trailing rip/quality tags on re-uploaded course parts, e.g.
# "课程开场-1080P 高清-AVC", "第3讲 4K", "lesson2-720P".
_QUALITY = re.compile(
    r"(?:[-_—\s]*)"
    r"(?:1080p|720p|480p|4k|8k|高清|超清|蓝光|avc|hevc|h\.?264|h\.?265|aac|完整版)"
    r"(?:[-_—\s].*)?$",
    re.IGNORECASE,
)

# Leading bare index such as "0 前言" / "01 课程介绍" (number + whitespace).
_INDEX_SPACE = re.compile(r"^(?:0{1,2}|\d{1,2})\s+(?=[一-鿿A-Za-z])")


def clean_part_title(title: str) -> str:
    """Strip numbering prefixes and trailing rip/quality tags from a 分P title."""
    t = title.strip()
    prev = None
    while prev != t:
        prev = t
        t = _QUALITY.sub("", t).strip(" -_—")
        t = _INDEX_SPACE.sub("", t, count=1)
        t = strip_title_prefixes(t)
    return t


def part_dedupe_key(title: str) -> str:
    t = clean_part_title(title)
    return re.sub(r"\s+", "", t).casefold()


def norm_for_match(title: str) -> str:
    t = clean_part_title(title)
    # Drop known source-noise bracketed tags but keep meaningful bracketed text.
    t = re.sub(
        r"【\s*(?:渡一教育|渡一|官方|完整版|高清|1080P|4K)\s*】"
        r"|\(\s*(?:渡一教育|渡一|官方|完整版|高清|1080P|4K)\s*\)"
        r"|（\s*(?:渡一教育|渡一|官方|完整版|高清|1080P|4K)\s*）",
        "", t, flags=re.IGNORECASE,
    )
    prev = None
    while prev != t:
        prev = t
        t = _NOISE.sub("", t).strip()
    t = re.sub(r"[\s\W_]+", "", t, flags=re.UNICODE)
    return t.casefold()


def load_kb_titles() -> list[tuple[str, str, str]]:
    """[(normalised title, display stem, relative path)] for every note file."""
    out: list[tuple[str, str, str]] = []
    if not KB_ROOT.exists():
        log(f"[warn] knowledge base not found: {KB_ROOT}")
        return out
    for p in KB_ROOT.rglob("*.md"):
        if ".git" in p.parts:
            continue
        stem = re.sub(r"\s*\(\d+\)$", "", p.stem)
        norm = norm_for_match(stem)
        if len(norm) >= 2:
            out.append((norm, stem, str(p.relative_to(KB_ROOT))))
    log(f"[kb] loaded {len(out)} note titles from {KB_ROOT}")
    return out


_BV_LINK = re.compile(
    r"https?://(?:www\.)?bilibili\.com/video/(BV[0-9A-Za-z]{10})(?:\?[^\s)\]>]*?\bp=(\d+))?"
)


def load_kb_bv_index() -> dict[tuple[str, int], str]:
    """(bvid, page) -> note path, parsed from 来源链接 lines inside KB notes.

    BiliNote writes one task per 分P, and a bare BV link means P1. This is an
    exact duplicate signal (the 渡一 合集 reuses the same BVs as older notes).
    """
    index: dict[tuple[str, int], str] = {}
    if not KB_ROOT.exists():
        return index
    for p in KB_ROOT.rglob("*.md"):
        if ".git" in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "bilibili.com/video/" not in text:
            continue
        rel = str(p.relative_to(KB_ROOT))
        for m in _BV_LINK.finditer(text):
            bv = m.group(1)
            page = int(m.group(2) or 1)
            index.setdefault((bv, page), rel)
    log(f"[kb] indexed {len(index)} BV links from note source lines")
    return index


def best_kb_match(norm: str, kb: list[tuple[str, str, str]]) -> tuple[float, str, str]:
    """Return (score, display_stem, relative_path) of the best candidate."""
    best = (0.0, "", "")
    if not norm:
        return best
    for knorm, stem, rel in kb:
        if not knorm:
            continue
        short, long_ = (norm, knorm) if len(norm) <= len(knorm) else (knorm, norm)
        if len(short) / len(long_) < 0.55:
            continue
        score = 0.0
        if short in long_:
            # Only treat containment as near-identical when the shorter title
            # covers most of the longer one; otherwise "network" would match
            # "network选项卡".
            coverage = len(short) / len(long_)
            if coverage >= 0.8:
                score = 0.90 + 0.10 * coverage
            else:
                sm = SequenceMatcher(None, norm, knorm)
                score = sm.ratio()
        else:
            sm = SequenceMatcher(None, norm, knorm)
            if sm.real_quick_ratio() < 0.82 or sm.quick_ratio() < 0.82:
                continue
            score = sm.ratio()
        if score > best[0]:
            best = (score, stem, rel)
            if score >= 0.999:
                break
    return best


KB_MATCH_THRESHOLD = 0.88
KB_MIN_FUZZY_LEN = 6


def is_kb_duplicate(norm: str, kb: list[tuple[str, str, str]]) -> tuple[bool, float, str, str]:
    if not norm:
        return False, 0.0, "", ""
    if len(norm) < KB_MIN_FUZZY_LEN:
        for knorm, stem, rel in kb:
            if norm == knorm:
                return True, 1.0, stem, rel
        return False, 0.0, "", ""
    score, stem, rel = best_kb_match(norm, kb)
    return score >= KB_MATCH_THRESHOLD, score, stem, rel


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def expand_parts(label: str, rows: list[dict], views: dict[str, dict]) -> list[dict]:
    """One item per 分P, deduped by normalised part title (first seen wins)."""
    seen: set[str] = set()
    items: list[dict] = []
    for v in rows:
        bv = v["bvid"]
        info = views.get(bv) or {"title": v["title"], "pages": []}
        pages = info.get("pages") or []
        video_title = info.get("title") or v["title"]
        if not pages:
            pages = [{"page": 1, "part": video_title, "duration": 0}]
        for p in pages:
            raw = (p.get("part") or "").strip()
            display = clean_part_title(raw) or raw
            key = part_dedupe_key(raw)
            if not key or key in seen:
                continue
            seen.add(key)
            multi = len(pages) > 1
            url = f"https://www.bilibili.com/video/{bv}"
            if multi:
                url += f"?p={p.get('page')}"
            items.append({
                "url": url,
                "bvid": bv,
                "page": p.get("page"),
                "part_title": display,
                "raw_part_title": raw,
                "video_title": video_title,
                "pubdate": info.get("pubdate", 0) or v.get("created", 0),
            })
    return items


def write_url_file(label: str, urls: list[str]) -> Path:
    path = GOAL / f"{label}.txt"
    path.write_text("\n".join(urls) + ("\n" if urls else ""), encoding="utf-8")
    return path


def build_source(src: dict, cookie: str | None, kb: list[tuple[str, str, str]],
                 kb_bvs: dict[tuple[str, int], str],
                 refresh: bool, fetch_only: bool) -> dict:
    label = src["label"]
    if src["kind"] == "space":
        rows = fetch_space(src["mid"], cookie, refresh)
    else:
        rows = fetch_list(src["mid"], src["sid"], cookie, refresh)
    log(f"[{label}] fetched {len(rows)} videos")

    stats: dict = {"label": label, "videos": len(rows), "written": 0,
                   "filters": [], "dropped_parts": [], "kb_drops": [], "kb_bv_drops": [],
                   "kb_near": []}

    if fetch_only:
        if src.get("parts") or src.get("kb_dedupe"):
            fetch_views(label, [v["bvid"] for v in rows], cookie, refresh)
        return stats

    selected = rows
    if src.get("since"):
        since_ts = _parse_since(src["since"])
        selected = [v for v in selected if v["created"] >= since_ts]
        stats["filters"].append(f"since {src['since']} -> {len(selected)}")
    if src.get("exclude"):
        pat = re.compile(src["exclude"], re.IGNORECASE)
        kept = []
        for v in selected:
            hit = pat.search(v["title"] or "")
            if hit:
                stats["dropped_parts"].append({
                    "title": v["title"], "bvid": v["bvid"], "reason": f"exclude:{hit.group(0)}",
                })
            else:
                kept.append(v)
        selected = kept
        stats["filters"].append(
            f"{src.get('exclude_label', 'exclude')} -> {len(selected)}")

    if src.get("parts") or src.get("kb_dedupe"):
        bvids = [v["bvid"] for v in selected]
        views = fetch_views(label, bvids, cookie, refresh)
        items = expand_parts(label, selected, views)
        stats["parts_total"] = len(items)
        if src.get("kb_dedupe"):
            kept_items = []
            for it in items:
                page = it["page"] or 1
                bv_hit = kb_bvs.get((it["bvid"], page))
                if bv_hit:
                    stats["kb_bv_drops"].append({
                        "part": it["part_title"],
                        "video": it["video_title"],
                        "bvid": it["bvid"],
                        "page": page,
                        "kb_path": bv_hit,
                    })
                    continue
                norm = norm_for_match(it["part_title"])
                dup, score, stem, rel = is_kb_duplicate(norm, kb)
                if dup:
                    stats["kb_drops"].append({
                        "part": it["part_title"],
                        "video": it["video_title"],
                        "bvid": it["bvid"],
                        "page": page,
                        "score": round(score, 3),
                        "kb_title": stem,
                        "kb_path": rel,
                    })
                else:
                    if score >= 0.75 and len(stats["kb_near"]) < 200:
                        stats["kb_near"].append({
                            "part": it["part_title"],
                            "video": it["video_title"],
                            "score": round(score, 3),
                            "kb_title": stem,
                            "kb_path": rel,
                        })
                    kept_items.append(it)
            stats["filters"].append(
                f"kb dedupe {len(items)} -> {len(kept_items)} "
                f"(bv={len(stats['kb_bv_drops'])}, title={len(stats['kb_drops'])})")
            items = kept_items
        urls = [it["url"] for it in items]
        stats["items"] = items
    else:
        urls = [f"https://www.bilibili.com/video/{v['bvid']}" for v in selected]

    path = write_url_file(label, urls)
    stats["written"] = len(urls)
    stats["path"] = str(path.relative_to(ROOT))
    log(f"[{label}] wrote {len(urls)} URLs -> {path}")
    return stats


def write_dedupe_report(stats: dict) -> None:
    if not (stats.get("kb_drops") or stats.get("dropped_parts")
            or stats.get("kb_bv_drops") or stats.get("kb_near")):
        return
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [f"# 去重报告：{stats['label']}", ""]
    if stats.get("filters"):
        lines += ["## 过滤", ""] + [f"- {f}" for f in stats["filters"]] + [""]
    if stats.get("kb_bv_drops"):
        lines += [f"## 与知识库 BV 相同而丢弃（{len(stats['kb_bv_drops'])}）", "",
                  "| 分P 标题 | 视频 | BV | 已有笔记 |", "|---|---|---|---|"]
        for d in stats["kb_bv_drops"]:
            lines.append(
                f"| {d['part']} | {d['video']} | {d['bvid']} P{d['page']} | {d['kb_path']} |")
        lines.append("")
    if stats.get("kb_drops"):
        lines += [f"## 与知识库标题相似而丢弃（{len(stats['kb_drops'])}）", "",
                  "| 分P 标题 | 视频 | 匹配笔记 | 相似度 |", "|---|---|---|---:|"]
        for d in stats["kb_drops"]:
            lines.append(
                f"| {d['part']} | {d['video']} | {d['kb_title']} | {d['score']} |")
        lines.append("")
    if stats.get("dropped_parts"):
        lines += [f"## 规则过滤（{len(stats['dropped_parts'])}）", "",
                  "| 标题 | BV | 原因 |", "|---|---|---|"]
        for d in stats["dropped_parts"]:
            lines.append(f"| {d['title']} | {d['bvid']} | {d['reason']} |")
        lines.append("")
    if stats.get("kb_near"):
        lines += [f"## 相似但保留（分数 >= 0.75，{len(stats['kb_near'])}）", "",
                  "这些标题接近知识库中已有笔记但未达到去重阈值，默认仍会解析。", "",
                  "| 分P 标题 | 相似度 | 已有笔记 |", "|---|---:|---|"]
        for d in stats["kb_near"]:
            lines.append(f"| {d['part']} | {d['score']} | {d['kb_title']} |")
        lines.append("")
    path = REPORT_DIR / f"{_safe_name(stats['label'])}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    log(f"[report] {path}")

    items = stats.get("items") or []
    if items:
        kept = [f"# 保留条目：{stats['label']}", "",
                f"共 {len(items)} 条（与去重报告同目录）", "",
                "| # | 分P 标题 | 视频 | URL |", "|---:|---|---|---|"]
        for i, it in enumerate(items, 1):
            kept.append(
                f"| {i} | {it['part_title']} | {it['video_title']} | {it['url']} |")
        kept_path = REPORT_DIR / f"{_safe_name(stats['label'])}_kept.md"
        kept_path.write_text("\n".join(kept) + "\n", encoding="utf-8")
        log(f"[report] {kept_path}")


def write_summary(all_stats: list[dict]) -> None:
    lines = ["# goal_videos 源清单生成摘要", "",
             f"生成时间：{datetime.now(BEIJING).strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)", "",
             "| 源 | 视频数 | 写出 URL 数 | 过滤/去重 |", "|---|---:|---:|---|"]
    for s in all_stats:
        filters = "；".join(s.get("filters") or []) or "-"
        lines.append(f"| {s['label']} | {s.get('videos', 0)} | {s.get('written', 0)} | {filters} |")
    lines.append("")
    path = GOAL / "_source_fetch_summary.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    log(f"[summary] {path}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Build per-source Bilibili URL lists from temp.txt sources")
    ap.add_argument("--only", default="", help="only sources whose label contains this substring")
    ap.add_argument("--refresh", action="store_true", help="ignore cached API data")
    ap.add_argument("--fetch-only", action="store_true", help="fetch/cache metadata but write no list files")
    ap.add_argument("--pending-only", action="store_true", help="only write 笔记待生成合集.txt")
    args = ap.parse_args()

    cookie = load_cookie()
    if not cookie:
        raise SystemExit(f"no bilibili cookie in {CONFIG}")
    log(f"cookie loaded ({len(cookie)} chars)")

    all_stats: list[dict] = []
    if not args.pending_only:
        sources = [s for s in SOURCES if not args.only or args.only in s["label"]]
        need_kb = any(s.get("kb_dedupe") for s in sources)
        kb = load_kb_titles() if need_kb else []
        kb_bvs = load_kb_bv_index() if need_kb else {}
        for src in sources:
            try:
                stats = build_source(src, cookie, kb, kb_bvs, args.refresh, args.fetch_only)
                all_stats.append(stats)
                write_dedupe_report(stats)
            except Exception as e:  # noqa: BLE001
                log(f"[ERROR] {src['label']}: {e}")
                all_stats.append({"label": src["label"], "videos": 0, "written": 0,
                                  "filters": [f"ERROR: {e}"]})

    if not args.fetch_only and not args.only:
        urls = [f"https://www.bilibili.com/video/{bv}" for bv in PENDING_BVS]
        path = write_url_file(PENDING_LABEL, urls)
        log(f"[{PENDING_LABEL}] wrote {len(urls)} URLs -> {path}")
        all_stats.append({"label": PENDING_LABEL, "videos": len(urls),
                          "written": len(urls), "filters": ["手动列出"]})
        write_summary(all_stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
