# BiliNote Style Comparison

Generated from BV1piKG6ZE2S (如何绕过网页反调试?【渡一教育】) using `qwen3.7-flash` on Qwen MaaS.

## Style Prompts

Each style appends a specific instruction to the LLM prompt (source: `app/gpt/prompt_builder.py`).

| Style | Prompt Text |
|---|---|
| `minimal` | 精简信息: 仅记录最重要的内容，简洁明了。 |
| `detailed` | 详细记录: 包含完整的内容和每个部分的详细讨论。需要尽可能多的记录视频内容，最好详细的笔记 |
| `academic` | 学术风格: 适合学术报告，正式且结构化。 |
| `tutorial` | 教程笔记: 尽可能详细的记录教程, 特别是关键点和一些重要的结论步骤 |
| `xiaohongshu` | 小红书风格: 擅长使用爆款关键词...采用二极管标题法...使用emoji... (long, ~300 chars) |
| `life_journal` | 生活向: 记录个人生活感悟，情感化表达。 |
| `task_oriented` | 任务导向: 强调任务、目标，适合工作和待办事项。 |
| `business` | 商业风格: 适合商业报告、会议纪要，正式且精准。 |
| `meeting_minutes` | 会议纪要: 适合商业报告、会议纪要，正式且精准。 |

## Output Comparison

| Style | Lines | Chars | Tone |
|---|---|---|---|
| `detailed` | ~60 | ~5,000 | Full depth, multi-level sub-points, trade-off analysis |
| `minimal` | 53 | 4,225 | Concise bullet points, no narrative fluff |
| `academic` | 53 | 4,148 | Formal structure, numbered sections, objective tone |
| `tutorial` | 50 | 5,276 | Step-by-step procedures, dense per line |
| `xiaohongshu` | 53 | 4,259 | Emoji-heavy, sensational headlines, buzzword-laden |
| `life_journal` | 48 | 5,016 | First-person narrative, reflective framing |
| `task_oriented` | 69 | 5,565 | Explicit task checklists, production workflow emphasis |
| `business` | 47 | 4,253 | Formal report, compact, risk/disclaimer notes |
| `meeting_minutes` | 55 | 5,044 | "纪要" format, discussion-style headings |

## Notable Observations

- **xiaohongshu** rewrites the title (e.g., "🔥你不学会这招绝对会后悔！") and uses terms like "教科书般操作", "神级技巧", "降维打击".
- **task_oriented** is the most comprehensive (69 lines, 5,565 chars) with an explicit "实战任务清单" checklist section.
- **tutorial** delivers the most actionable content per line — high information density.
- **business** and **meeting_minutes** share the **exact same prompt text** in the codebase (`prompt_builder.py:83-84`) — a copy-paste oversig
  - Their outputs are nearly identical for this video.
- **life_journal** adds first-person narrative: "作为一名前端开发者，我最近在研究...".

## Recommendation for Lesson/Tutorial Videos

### Tier 1 — Best fit

| Style | Why |
|---|---|
| `tutorial` | Prompt explicitly targets tutorials. Highest information density per line. Best for coding/dev lessons where steps and conclusions matter. |
| `task_oriented` | Most comprehensive output. Includes actionable checklists. Good when the viewer needs to *do* something after watching. |

### Tier 2 — Solid, generic

| Style | Why |
|---|---|
| `detailed` | Good all-rounder. Deep coverage but slightly more narrative than `tutorial`. |
| `academic` | Similar to `detailed` in output. The prompt difference ("正式且结构化") doesn't shift behavior much for technical content. |

### Tier 3 — Wrong fit for lessons

| Style | Why |
|---|---|
| `minimal` | Loses nuance. OK for quick scanning, not for learning. |
| `business` / `meeting_minutes` | Too terse. Identical prompts produce near-identical output. |
| `life_journal` | First-person narrative framing distracts from technical content. |
| `xiaohongshu` | Viral emoji + sensational headline format actively fights learning. Fun but poor reference material. |
| `meeting_minutes` | Same prompt as `business` — a likely bug in the codebase. |
