#!/usr/bin/env python3
"""Classify the deduplicated 分P titles of 程序员方格 (2026) by topic.

Input is the JSON produced by ``fetch_video_pages.py``. The script re-runs the
same normalisation/dedup used for ``temp_parts_unique_2026.txt`` and maps each
unique 分P to one topic bucket.

Classification strategy:
  1. match the 分P title against topic keywords (ordered, specific first);
  2. if the part title is short/ambiguous and the parent video is a dedicated
     topic collection (e.g. its title contains "React" / "VUE" / "TypeScript"),
     use that topic as a fallback;
  3. otherwise put it in 综合与其他.

Outputs:
  goal_videos/程序员方格_分P分类.json          structured result
  goal_videos/程序员方格_分P分类.md            readable report
  goal_videos/程序员方格_分类URL/<slug>.txt   one URL per line (batch input)
  goal_videos/程序员方格_分类URL/_manifest.json

Run from backend/:
    python script/pagination_query/classify_programmer_fangge.py
"""
from __future__ import annotations

import json
import re
from collections import OrderedDict
from pathlib import Path

from fetch_video_pages import strip_title_prefixes

BACKEND = Path(__file__).resolve().parents[2]
ROOT = BACKEND.parent
GOAL = ROOT / "goal_videos"
SRC = GOAL / "temp_pages_2026.json"
OUT_JSON = GOAL / "程序员方格_分P分类.json"
OUT_MD = GOAL / "程序员方格_分P分类.md"
OUT_URL_DIR = GOAL / "程序员方格_分类URL"


# ---------------------------------------------------------------------------
# Topic buckets (ordered: first match wins)
# ---------------------------------------------------------------------------

CATEGORIES: list[dict] = [
    {
        "slug": "01-简历与求职",
        "label": "简历与求职",
        "patterns": [
            r"简历", r"求职", r"就业指导", r"刷题路线", r"职业规划", r"跳槽",
            r"涨薪", r"工作经历", r"项目经验", r"自我评价", r"兴趣爱好",
            r"证书", r"技术栈", r"STAR法则", r"校园项目",
            r"\d+\s*年.*经验", r"专科", r"学历",
        ],
    },
    {
        "slug": "02-微前端",
        "label": "微前端",
        "patterns": [
            r"微前端", r"qiankun", r"single[- ]?spa", r"wujie", r"无界",
            r"module\s*federation", r"MF", r"iframe", r"JS\s*隔离", r"样式隔离",
            r"shared配置", r"共享机制",
        ],
    },
    {
        "slug": "03-React",
        "label": "React",
        "patterns": [
            r"react", r"jsx", r"hook", r"usestate", r"useeffect", r"usememo",
            r"usecallback", r"useref", r"usereducer", r"usecontext", r"usetransition",
            r"uselayouteffect", r"redux", r"mobx", r"zustand", r"jotai", r"immer",
            r"rtk", r"next\.js", r"fiber", r"workinprogress", r"合成事件", r"setstate",
            r"错误边界", r"error boundar", r"受控组件", r"高阶组件", r"\bHOC\b",
            r"虚拟\s*DOM", r"forwardref", r"imperativehandle", r"hydration", r"注水",
            r"react[- ]?router", r"react\s*query", r"\bSWR\b", r"react\s*hook\s*form",
            r"原子设计", r"atomic design", r"SSR", r"CSR", r"服务端渲染",
            r"受保护的路由", r"protected route", r"UI\s*=\s*f\(", r"props", r"组件库",
            r"testing library", r"jest", r"vitest", r"mock", r"生命周期",
            r"状态管理", r"列表组件key", r"key作用",
        ],
    },
    {
        "slug": "04-Vue",
        "label": "Vue",
        "patterns": [
            r"vue", r"vuex", r"pinia", r"vue[- ]?router", r"composition[- ]?api",
            r"options\s*api", r"响应式(系统|原理|更新|陷阱)", r"双向数据绑定",
            r"v-if", r"v-show", r"v-for", r"v-model", r"v-bind", r"slot", r"插槽",
            r"teleport", r"provide[- ]?inject", r"nexttick", r"自定义指令",
            r"mixin", r"watcheffect", r"torefs?", r"toRefs?", r"reactiveref",
            r"数据劫持", r"模板编译", r"diff\s*算法", r"组件封装", r"组件通信",
            r"父子组件", r"组件传参",
        ],
    },
    {
        "slug": "05-TypeScript",
        "label": "TypeScript",
        "patterns": [
            r"typescript", r"(?<![A-Za-z])TS(?![A-Za-z])", r"tsconfig", r"类型别名", r"泛型", r"类型体操",
            r"类型层级", r"联合类型", r"交叉类型", r"接口\s*\(interfaces\)", r"扩展接口",
            r"any\s*和\s*unknown", r"枚举\s*enum", r"声明合并", r"抽象类",
            r"访问修饰符", r"实用工具类型", r"内置的工具类型", r"元组\s*\(tuple\)",
            r"类型断言", r"类型守卫", r"基础类型", r"对象类型", r"函数重载",
            r"剩余参数", r"特殊类型",
        ],
    },
    {
        "slug": "06-手写代码与算法",
        "label": "手写代码与算法",
        "patterns": [
            r"手写", r"手撕", r"手动实现", r"实现数组", r"A\+", r"符合.*promise",
            r"实现.*(bind|call|apply|new|instanceof)", r"笔试题", r"代码修改",
            r"代码面试题", r"逻辑编程题", r"算法", r"数据结构", r"LRU", r"排序",
            r"数组去重", r"去重", r"深克隆", r"EventEmitter", r"发布订阅", r"柯里化",
            r"compose", r"pipe", r"大数相加", r"洗牌", r"采样", r"并发控制",
            r"请求重试", r"防抖", r"节流", r"千位", r"千分位", r"sleep",
            r"递归", r"遍历算法", r"深度优先", r"广度优先", r"二叉树", r"链表",
            r"两数组交集", r"清除字符串前后空格", r"字符串翻转", r"字符串重复",
            r"编程题", r"百度面试题",
        ],
    },
    {
        "slug": "07-异步编程与Promise",
        "label": "异步编程与 Promise",
        "patterns": [
            r"promise", r"async", r"await", r"事件循环", r"event\s*loop", r"宏任务",
            r"微任务", r"回调地狱", r"异步", r"generator", r"settimeout",
            r"setinterval", r"requestanimationframe", r"requestidlecallback",
        ],
    },
    {
        "slug": "08-Nodejs与服务端",
        "label": "Node.js 与服务端",
        "patterns": [
            r"node(\.js)?", r"express", r"koa", r"nest",
            r"fs模块", r"服务器", r"路由配置", r"登录注册", r"数据库", r"mysql",
            r"redis", r"mongodb", r"nginx", r"docker", r"后端",
        ],
    },
    {
        "slug": "09-HTML",
        "label": "HTML",
        "patterns": [
            r"html", r"doctype", r"语义化", r"script元素", r"script.*阻塞",
            r"行内与外部代码", r"文档模式", r"字符集", r"meta\s*标签", r"标签",
        ],
    },
    {
        "slug": "10-CSS与布局",
        "label": "CSS 与布局",
        "patterns": [
            r"css", r"BFC", r"盒模型", r"flex", r"grid", r"position", r"float",
            r"z-?index", r"containing block", r"选择器", r"优先级", r"权重",
            r"继承与计算值", r"外边距", r"margin", r"padding", r"水平垂直居中",
            r"inline-block", r"响应式布局", r"媒体查询", r"雪碧图", r"多行溢出",
            r"伪元素", r"伪类", r"nth-child", r"布局", r"元素隐藏", r"隐藏方式",
            r"透明", r"文字重叠", r"格式化上下文",
        ],
    },
    {
        "slug": "11-性能优化",
        "label": "性能优化",
        "patterns": [
            r"性能", r"优化", r"web\s*指标", r"web\s*vitals", r"\bLCP\b", r"\bFID\b", r"\bCLS\b",
            r"首屏", r"白屏", r"懒加载", r"延迟加载", r"预加载", r"资源提示符",
            r"图片.*优化", r"图像.*优化", r"字体.*优化", r"骨架屏", r"spinner",
            r"长任务", r"代码分割", r"打包体积", r"will-change", r"transform",
            r"opacity", r"动画性能", r"1px", r"卡顿", r"页面为什么会卡",
            r"CDN", r"cdn", r"server\s*worker", r"service\s*worker",
            r"重排", r"重绘", r"回流", r"布局抖动",
        ],
    },
    {
        "slug": "12-网络与安全",
        "label": "网络与安全",
        "patterns": [
            r"http", r"https", r"tcp", r"udp", r"quic", r"网络", r"tls", r"ssl",
            r"证书", r"握手", r"状态码", r"强缓存", r"协商缓存", r"http.*缓存",
            r"浏览器缓存", r"ajax", r"xhr", r"xmlhttprequest", r"fetch", r"jsonp",
            r"跨域", r"xss", r"csrf", r"安全", r"攻击", r"加密", r"token", r"jwt",
            r"dns", r"域名", r"websocket", r"sse", r"socket",
            r"多路复用", r"滑动窗口", r"拥塞控制", r"长连接", r"短连接",
            r"同源策略", r"中间人",
        ],
    },
    {
        "slug": "13-浏览器原理",
        "label": "浏览器原理",
        "patterns": [
            r"浏览器", r"渲染(过程|流程|模式|原理)", r"页面是怎么画", r"页面加载",
            r"重排", r"重绘", r"回流", r"布局抖动", r"合成层", r"composite",
            r"GPU", r"indexeddb", r"localstorage", r"sessionstorage", r"cookie",
            r"web worker", r"pwa", r"浏览器内核", r"浏览器的一生",
        ],
    },
    {
        "slug": "14-工程化与构建",
        "label": "工程化与构建",
        "patterns": [
            r"webpack", r"vite", r"babel", r"rollup", r"esbuild", r"构建",
            r"打包", r"模块化", r"commonjs", r"\bAMD\b", r"\bCMD\b", r"\bUMD\b",
            r"\bESM\b", r"es6\s*转\s*es5", r"热更新", r"\bnpm\b", r"pnpm",
            r"第三方\s*npm", r"环境变量", r"vue-cli", r"脚手架", r"monorepo",
            r"eslint", r"prettier", r"source\s*map", r"loader", r"plugin",
            r"tree\s*shaking", r"lodash", r"handlebars|handlerbars", r"backbone",
            r"\bnpm\b", r"pnpm", r"yarn", r"模块安装", r"vscode", r"终端",
        ],
    },
    {
        "slug": "15-JavaScript基础",
        "label": "JavaScript 基础",
        "patterns": [
            r"javascript", r"\bJS\b", r"es6", r"es5", r"ecmascript", r"\bvar\b",
            r"\blet\b", r"\bconst\b", r"==", r"变量", r"数据类型", r"typeof",
            r"类型转换", r"隐式转换", r"强制类型转换", r"值类型", r"引用类型",
            r"堆和栈", r"包装类型", r"原型", r"构造函数", r"new\s*(操作符|关键字)",
            r"instanceof", r"继承", r"class", r"this", r"call", r"apply", r"bind",
            r"闭包", r"作用域", r"预解析", r"变量提升", r"函数", r"箭头函数",
            r"IIFE", r"立即执行", r"纯函数", r"函数式编程", r"数组", r"对象",
            r"字符串", r"number", r"string", r"boolean", r"symbol", r"bigint",
            r"map", r"set", r"weakmap", r"weakset", r"date", r"regexp", r"正则",
            r"json", r"dom", r"bom", r"window", r"事件", r"target", r"currenttarget",
            r"mouseover", r"mouseenter", r"click", r"touch", r"语句", r"语法",
            r"关键字", r"保留字", r"操作符", r"解构", r"模板字符串", r"严格模式",
            r"rest参数", r"扩展运算符", r"迭代", r"遍历器", r"设计模式",
            r"面向对象", r"创建对象", r"属性", r"undefined", r"null", r"nan",
            r"0\.1", r"浮点数", r"精度", r"短路", r"前缀", r"后缀", r"数组方法",
            r"数组常用方法", r"伪数组", r"真数组", r"类数组", r"清空数组",
            r"数组合并", r"深浅拷贝", r"object\.create", r"object", r"new\s*操作符",
            r"定时器", r"垃圾回收", r"执行上下文", r"作用域链", r"内存泄漏",
            r"V8", r"内存回收", r"函数表达式", r"函数声明", r"创建函数", r"预解析",
            r"this指向", r"原始值", r"url参数", r"解析url", r"function", r"foreach",
            r"for\.\.\.in", r"for\.\.\.of", r"强转", r"隐转", r"集合类型",
            r"页面输出", r"阻止默认行为", r"return false", r"输出题|输出面试题|输出0-9",
            r"验证网址", r"静态成员", r"实例成员", r"defineproperty", r"let的基本使用",
            r"let使用注意点", r"js运行机制", r"js引擎", r"随机数生成", r"短路赋值",
        ],
    },
    {
        "slug": "16-场景题与方案设计",
        "label": "场景题与方案设计",
        "patterns": [
            r"场景", r"如何", r"怎么", r"设计", r"方案", r"架构", r"选型",
            r"权限", r"水印", r"拖拽", r"轮播", r"弹窗", r"上传", r"截图",
            r"埋点", r"监控", r"降级", r"主题切换", r"防重复提交", r"联调",
            r"从0到1", r"大文件", r"并发请求", r"进度", r"上拉加载", r"下拉刷新",
            r"移动端", r"h5", r"AI", r"\bmcp\b", r"chatgpt", r"canvas",
            r"图形", r"坐标", r"检测", r"调试", r"错误", r"拦截", r"首页白屏",
            r"超大数据", r"任务列表", r"数据存储对象", r"自主设计", r"路由原理",
            r"前端路由", r"静态资源", r"防抖.*应用", r"节流.*应用",
            r"防止按钮重复提交", r"多并发", r"input搜索", r"状态管理区别",
            r"状态管理中同步",
        ],
    },
    {
        "slug": "17-综合与其他",
        "label": "综合与其他",
        "patterns": [],
    },
]


# Dedicated collection title -> category. Only explicit topic collections are
# listed; generic titles like "100道前端面试题" intentionally have no hint.
VIDEO_HINTS: list[tuple[str, str]] = [
    ("03-React", r"react"),
    ("04-Vue", r"\bvue\b"),
    ("05-TypeScript", r"typescript|(?<![A-Za-z])TS(?![A-Za-z])"),
    ("06-手写代码与算法", r"手写代码|手撕代码"),
    ("07-异步编程与Promise", r"异步编程"),
    ("08-Nodejs与服务端", r"node\.?js|\bnode\b"),
    ("11-性能优化", r"性能优化"),
    ("14-工程化与构建", r"工程化"),
    ("02-微前端", r"微前端"),
    ("01-简历与求职", r"简历定制|简历优化|简历修改|改简历|简历照着改|就业指导|求职"),
    ("15-JavaScript基础", r"javascript"),
    ("09-HTML", r"html"),
    ("10-CSS与布局", r"css"),
]

# Weak buckets that may be overridden by a dedicated collection's topic.
_WEAK_BUCKETS = {"15-JavaScript基础", "16-场景题与方案设计", "17-综合与其他"}

# If a part matched 手写 solely because of a generic word, a dedicated
# framework/engineering collection may claim it (e.g. "实现受保护的路由").
_CODING_STRONG = re.compile(
    r"手写|手撕|promise|数组|深克隆|深拷贝|EventEmitter|柯里化|防抖|节流|"
    r"LRU|算法|bind|call|apply|new|instanceof|compose|pipe|大数|洗牌|"
    r"并发控制|请求重试|千位|千分位|sleep|扁平化|去重|排序|递归|"
    r"笔试题|代码修改|代码面试题|逻辑编程题|手动实现",
    re.IGNORECASE,
)


# Prefixes that are section labels rather than part of the topic. They are
# stripped only for matching (display titles keep them). Note: bare "React-"
# is deliberately NOT stripped, otherwise "React-router" loses its topic.
_SECTION_PREFIX = re.compile(
    r"^(?:"
    r"React篇|VUE篇|Vue篇|Javascript篇|JavaScript篇|TypeScript篇|HTML篇|CSS篇|"
    r"性能优化篇|微前端篇|手写代码篇|手撕代码题|异步编程篇|工程化篇|JS篇|TS篇|"
    r"场景题"
    r")\s*[-－—_:：]\s*",
    re.IGNORECASE,
)
_COURSE_PREFIX = re.compile(r"^课程\s*\d+\s*[-－—_:：]\s*")

# The "XX篇-" label of a part is also a reliable topic hint.
_SECTION_HINTS: list[tuple[str, str]] = [
    ("03-React", r"^React篇\s*[-－—_:：]"),
    ("04-Vue", r"^VUE篇|^Vue篇"),
    ("15-JavaScript基础", r"^Javascript篇|^JavaScript篇|^JS篇"),
    ("05-TypeScript", r"^TypeScript篇|^TS篇"),
    ("09-HTML", r"^HTML篇"),
    ("10-CSS与布局", r"^CSS篇"),
    ("11-性能优化", r"^性能优化篇"),
    ("02-微前端", r"^微前端篇"),
    ("06-手写代码与算法", r"^手写代码篇"),
    ("07-异步编程与Promise", r"^异步编程篇"),
    ("14-工程化与构建", r"^工程化篇"),
]


def clean_for_match(title: str) -> str:
    t = strip_title_prefixes(title)
    previous = None
    while previous != t:
        previous = t
        t = _SECTION_PREFIX.sub("", t, count=1)
        t = _COURSE_PREFIX.sub("", t, count=1)
        t = strip_title_prefixes(t)
    return t.strip()


def section_hint(title: str) -> str | None:
    for slug, pat in _SECTION_HINTS:
        if re.search(pat, title.strip(), re.IGNORECASE):
            return slug
    return None


def classify_by_title(text: str) -> tuple[str, str]:
    low = text.lower()
    for cat in CATEGORIES:
        for pat in cat["patterns"]:
            if re.search(pat, low, re.IGNORECASE):
                return cat["slug"], f"title:{pat}"
    return "17-综合与其他", "fallback"


def video_hint(video_title: str) -> str | None:
    """Topic of a dedicated collection, or None for mixed interview videos."""
    low = video_title.lower()
    # A title that names both HTML and CSS is mixed; let the part title decide.
    if re.search(r"html", low) and re.search(r"css", low):
        return None
    for slug, pat in VIDEO_HINTS:
        if re.search(pat, low, re.IGNORECASE):
            return slug
    return None


def classify(title: str, video_title: str) -> tuple[str, str]:
    text = clean_for_match(title)
    slug, reason = classify_by_title(text)
    hints = [(section_hint(title), "section"), (video_hint(video_title), "video")]

    for hint, source in hints:
        if not hint or hint == slug:
            continue
        if slug in _WEAK_BUCKETS:
            return hint, f"{source}:{hint}"
        if slug == "06-手写代码与算法" and not _CODING_STRONG.search(text):
            return hint, f"{source}:{hint}"
    return slug, reason


def collect_unique(videos: list[dict]) -> list[dict]:
    """Same key as fetch_video_pages.dedupe_titles, newest video first."""
    seen: set[str] = set()
    items: list[dict] = []
    for v in videos:
        for p in v["pages"]:
            raw = (p.get("part") or "").strip()
            display = strip_title_prefixes(raw)
            key = re.sub(r"\s+", "", display)
            if not key or key in seen:
                continue
            seen.add(key)
            items.append({
                "title": display,
                "raw_title": raw,
                "url": f"https://www.bilibili.com/video/{v['bvid']}?p={p['page']}",
                "bvid": v["bvid"],
                "page": p["page"],
                "duration": p.get("duration") or 0,
                "video_title": v["title"],
                "pubdate": v.get("pubdate", 0),
            })
    return items


def main() -> int:
    videos = json.loads(SRC.read_text(encoding="utf-8"))
    items = collect_unique(videos)

    by_slug: "OrderedDict[str, list[dict]]" = OrderedDict((c["slug"], []) for c in CATEGORIES)
    for item in items:
        slug, reason = classify(item["title"], item["video_title"])
        item["category"] = slug
        item["reason"] = reason
        by_slug[slug].append(item)

    OUT_JSON.write_text(
        json.dumps(
            {
                "source": str(SRC.relative_to(ROOT)).replace("\\", "/"),
                "total": len(items),
                "categories": [
                    {
                        "slug": c["slug"],
                        "label": c["label"],
                        "count": len(by_slug[c["slug"]]),
                        "items": by_slug[c["slug"]],
                    }
                    for c in CATEGORIES
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    OUT_URL_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for c in CATEGORIES:
        slug = c["slug"]
        rows = by_slug[slug]
        (OUT_URL_DIR / f"{slug}.txt").write_text(
            "\n".join(r["url"] for r in rows) + ("\n" if rows else ""), encoding="utf-8"
        )
        manifest.append({"slug": slug, "label": c["label"], "count": len(rows),
                         "urls_file": f"{slug}.txt"})
    (OUT_URL_DIR / "_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# 程序员方格 2026 分P 分类",
        "",
        f"- 去重后分P 总数：{len(items)}",
        f"- 分类数：{len(CATEGORIES)}",
        "",
        "| 分类 | 数量 |",
        "|---|---:|",
    ]
    for c in CATEGORIES:
        lines.append(f"| {c['label']} | {len(by_slug[c['slug']])} |")
    lines.append("")

    for c in CATEGORIES:
        rows = by_slug[c["slug"]]
        if not rows:
            continue
        lines.append(f"## {c['label']}（{len(rows)}）")
        lines.append("")
        for i, r in enumerate(rows, 1):
            minutes, seconds = divmod(int(r["duration"]), 60)
            lines.append(
                f"{i}. [{r['title']}]({r['url']}) "
                f"`{r['bvid']} P{r['page']}` `{minutes}:{seconds:02d}`"
            )
        lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"total={len(items)}")
    for c in CATEGORIES:
        print(f"{c['slug']}: {len(by_slug[c['slug']])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
