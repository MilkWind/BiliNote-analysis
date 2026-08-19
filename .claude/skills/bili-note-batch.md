---
name: bili-note-batch
description: Batch process Bilibili videos into AI-generated notes — confirms transcriber engine and per-request settings (style, format, provider/model, video understanding), submits and monitors tasks.
---

# BiliNote Batch Processing

## Pre-condition

Backend must be running. Quick check:
```bash
curl -s http://localhost:8483/api/get_all_providers | python -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('code')==0 else 'DOWN')"
```

If not, run `bili-note-init`.

### Bilibili Cookie

Bilibili videos require login cookies for reliable download. Without cookies, yt-dlp returns HTTP 412 and audio extraction fails. **Required for `video_understanding: true`** (video download needs auth) and strongly recommended for all bilibili tasks.

Check current cookie status:
```bash
curl -s http://localhost:8483/api/get_downloader_cookie/bilibili | python -c "import sys,json; d=json.load(sys.stdin); print('SET' if d.get('data') and d['data'].get('cookie') else 'MISSING')"
```

If `MISSING`, ask the user for their bilibili cookies. Open bilibili.com in a logged-in browser, then copy the full cookie string from DevTools → Application → Cookies → bilibili.com → right-click any cookie → "Copy all". The cookie **must include `SESSDATA`** — this is the session auth token. Without it, downloads will fail.

Set the cookie:
```bash
curl -s -X POST http://localhost:8483/api/update_downloader_cookie \
  -H "Content-Type: application/json" \
  -d '{"platform": "bilibili", "cookie": "<full-cookie-string>"}'
```

Or ask the user to configure it via Settings page in the frontend (`http://localhost:3015`).

## Phase 1 — Choose Transcriber Engine

The transcriber is a **global setting** (applies to all tasks in the batch). Confirm it before submitting.

Check the current engine:
```bash
curl -s http://localhost:8483/api/transcriber_config | python -c "import sys,json; d=json.load(sys.stdin)['data']; print('transcriber:', d['transcriber_type'], '| whisper model:', d['whisper_model_size'])"
```

Ask the user which engine to use. Available options:

| Value | Label | Key / Model required |
|---|---|---|
| `volc-seedasr` | 火山引擎 SeedASR（在线） | `VOLC_SEEDASR_API_KEY` in `.env` |
| `groq` | Groq（在线） | Groq API key in provider config |
| `bcut` | 必剪（在线） | none |
| `kuaishou` | 快手（在线） | none |
| `fast-whisper` | Faster Whisper（本地） | local model download (default `tiny`) |
| `mlx-whisper` | MLX Whisper（仅macOS） | macOS only |

Switch engine (persisted to `backend/config/transcriber.json`, takes effect on the **next** task — no code change or backend restart needed to switch engines):
```bash
curl -s -X POST http://localhost:8483/api/transcriber_config \
  -H "Content-Type: application/json" \
  -d '{"transcriber_type": "<TYPE>"}' | python -m json.tool
```

Caveats:
- **`volc-seedasr`**: if `VOLC_SEEDASR_API_KEY` is not set in `.env`, transcription fails with `VOLC_SEEDASR_API_KEY 未配置`. Adding the key requires editing `.env` and **restarting the backend** — the key is read once at transcriber init.
- **Online engines** (`volc-seedasr`, `groq`, `bcut`, `kuaishou`) are always ready — no local model download.
- **`fast-whisper` / `mlx-whisper`** need their model downloaded first; a batch against a missing model fails with `转写模型 ... 尚未下载就绪` (download via `POST /api/transcriber_download` or the frontend settings page).

## Phase 2 — Confirm Per-Request Settings

Ask these four things before submitting.

### 1. 笔记风格 (style)

| Value | Label |
|---|---|
| `detailed` | 详细 |
| `minimal` | 精简 |
| `academic` | 学术 |
| `tutorial` | 教程 |
| `xiaohongshu` | 小红书 |
| `life_journal` | 生活向 |
| `task_oriented` | 任务导向 |
| `business` | 商业风格 |
| `meeting_minutes` | 会议纪要 |

### 2. 笔记格式 (format) — multi-select

Ask: "需要包含哪些？目录、原片跳转、原片截图、AI总结？"

| Value | Label | Effect |
|---|---|---|
| `toc` | 目录 | TOC from `##` headings |
| `link` | 原片跳转 | `*Content-[mm:ss]` timestamps |
| `screenshot` | 原片截图 | `*Screenshot-[mm:ss]` markers |
| `summary` | AI总结 | `## AI 总结` section |

### 3. 供应商 & 模型 (provider & model)

```bash
# Providers and key status
curl -s http://localhost:8483/api/get_all_providers | python -c "
import sys,json
for p in json.load(sys.stdin)['data']:
    has_key = 'SET' if p.get('api_key') else 'MISSING'
    print(f'{p[\"id\"]}: key={has_key}')
"

# Models for chosen provider
curl -s http://localhost:8483/api/model_list/<provider_id> | python -c "
import sys,json
for m in json.load(sys.stdin)['data']['models']:
    print(f'  - {m[\"id\"]}')
"
```

Must have an API key configured. Query models at runtime — names change.

### 4. 视频理解模型 (video_understanding)

Default `false`. Ask: "是否启用视频理解模型？（不强求启用）"

If yes, also set:
- `video_interval`: 截帧间隔（秒），default 30
- `grid_size`: 缩略图网格，e.g. `[4, 4]`

**Important**: Video understanding requires downloading the full video file (not just audio). For bilibili, this means **bilibili cookies with SESSDATA must be configured** (see Pre-condition above). Without valid login cookies, the video download will fail with HTTP 412. The chosen model must also be vision-capable (e.g. `qwen-vl-plus`, `qwen3-vl-flash`, `gpt-4o`).

### 5. 模型选择注意事项

Video understanding requires a **single model** that accepts both text and images (vision-language model). The same model handles transcript summarization AND frame analysis in one call — there is no split-provider pipeline.

- `video_understanding: false` → any model works (text-only is fine)
- `video_understanding: true` → must pick a vision-capable model (e.g., `qwen-vl-plus`, `qwen3-vl-flash`, `gpt-4o`)

On Qwen MaaS, check available VL models:
```bash
curl -s http://localhost:8483/api/model_list/qwen | python -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin)['data']['models']]" | grep -iE 'vl|vision'
```

## Phase 3 — Locate Video List

Common locations:
- `goal_videos/*.txt`
- `urls.txt`

```bash
grep -c 'http' <file>
```

## Phase 4 — Verify One Task First

```bash
curl -s -X POST http://localhost:8483/api/generate_note \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "<first URL>",
    "platform": "bilibili",
    "quality": "fast",
    "model_name": "<MODEL>",
    "provider_id": "<PROVIDER>",
    "style": "<STYLE>",
    "format": [...],
    "screenshot": false,
    "link": false,
    "video_understanding": false
  }' | python -m json.tool
```

Wait 30-60s:
```bash
curl -s http://localhost:8483/api/task_status/<task_id> | python -m json.tool
```

If RUNNING, configuration is correct. If failed immediately, fix before proceeding.

## Phase 5 — Submit Batch

```bash
count=0
while IFS= read -r url; do
  [ -z "$url" ] && continue
  curl -s -X POST http://localhost:8483/api/generate_note \
    -H "Content-Type: application/json" \
    -d "{\"video_url\": \"$url\", \"platform\": \"bilibili\", \"quality\": \"fast\", \"model_name\": \"MODEL\", \"provider_id\": \"PROVIDER\", \"style\": \"STYLE\", \"format\": [...], \"screenshot\": false, \"link\": false, \"video_understanding\": false}" \
    | python -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('task_id','ERROR'))"
  count=$((count+1))
  echo "Submitted: $count"
done < urls.txt
```

~1-2s per task. Resume interrupted batch: `tail -n +<line> urls.txt`.

## Phase 6 — Monitor Progress

```bash
cd backend/note_results
echo "Success: $(grep -l '"status": "SUCCESS"' *.status.json 2>/dev/null | wc -l)"
echo "Failed:  $(grep -l '"status": "FAILED"' *.status.json 2>/dev/null | wc -l)"
echo "Running: $(grep -l '"status": "RUNNING"' *.status.json 2>/dev/null | wc -l)"
echo "Pending: $(grep -l '"status": "PENDING"' *.status.json 2>/dev/null | wc -l)"
```

Output files:
- `{task_id}_markdown.md` — generated note
- `{task_id}.json` — full data
- `{task_id}_transcript.json` — raw transcript
- `{task_id}.status.json` — status

Git Bash garbles Chinese output. Read files directly.

## Request Payload Reference

```json
{
  "video_url": "https://www.bilibili.com/video/BVxxx",
  "platform": "bilibili",
  "quality": "fast",
  "model_name": "<model_from_provider>",
  "provider_id": "<provider_id>",
  "style": "academic",
  "format": ["toc", "link"],
  "screenshot": false,
  "link": false,
  "video_understanding": false,
  "video_interval": 30,
  "grid_size": [4, 4],
  "task_id": null,
  "extras": null,
  "prefetched_transcript": null
}
```

## Common Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| `API Key 未配置` | Provider key not set | Run `bili-note-init` |
| `ffprobe and ffmpeg not found` | FFmpeg missing | Set `FFMPEG_BIN_PATH` in `.env`, restart backend |
| Transcriber model not ready | fast-whisper model not downloaded | Download model or switch to `bcut` |
| Task stuck PENDING | Queue full | Wait, or increase `TASK_MAX_WORKERS` |
| `HTTP Error 412: Precondition Failed` | Bilibili requires auth | Set bilibili cookie with SESSDATA (see Pre-condition) |
| `unable to obtain file audio codec with ffprobe` | Bilibili download blocked (no cookie) or rate-limited | Set valid bilibili cookies, avoid submitting many tasks for the same video simultaneously |
