# BiliNote Batch Processing Guide

Lessons from the 2026-08-11 batch processing of 82 Bilibili videos.

## Pre-flight Checklist

### 1. Confirm Style & Format with User

**Before submitting any tasks**, explicitly confirm two things:

#### 笔记风格 (style)

| Value | Label |
|---|---|
| `minimal` | 精简 |
| `detailed` | 详细 |
| `academic` | 学术 |
| `tutorial` | 教程 |
| `xiaohongshu` | 小红书 |
| `life_journal` | 生活向 |
| `task_oriented` | 任务导向 |
| `business` | 商业风格 |
| `meeting_minutes` | 会议纪要 |

Pass as `"style": "detailed"`.

#### 笔记格式 (format) — a JSON array, controls what extras appear in the note

| Value | Label | Effect |
|---|---|---|
| `toc` | 目录 | Auto-generate table of contents from `##` headings |
| `link` | 原片跳转 | Add `*Content-[mm:ss]` timestamps per section |
| `screenshot` | 原片截图 | Add `*Screenshot-[mm:ss]` markers where screenshots help |
| `summary` | AI总结 | Append `## AI 总结` section at the end |

Pass as `"format": ["toc", "link", "summary"]` — only include what the user wants.

**Prompt the user**: "你需要笔记包含哪些？目录、原片跳转、原片截图、AI总结？"

Never assume defaults — ask if the user hasn't specified.

### 2. Verify Prerequisites

Run these checks before batch submission:

```bash
# Check FFmpeg
curl -s http://localhost:8483/api/health  # or just try starting backend

# Check .env has FFMPEG_BIN_PATH
cat .env | grep FFMPEG_BIN_PATH
```

If FFmpeg is missing, all tasks fail instantly at download stage.

### 3. Configure API Key First

Tasks fail immediately if the provider has no API key configured. A batch of 82 tasks can all fail in seconds because the key check happens before any heavy work.

```bash
# Set API key BEFORE submitting tasks
curl -X POST http://localhost:8483/api/update_provider \
  -H "Content-Type: application/json" \
  -d '{"id": "deepseek", "api_key": "sk-xxx"}'

# Verify
curl -s http://localhost:8483/api/model_list/deepseek
```

### 4. Restart Backend After Config Changes

If the backend was started without FFmpeg or API key, kill and restart it:

```bash
# Kill old process on port 8483
netstat -ano | grep 8483
taskkill //PID <pid> //F

# Start fresh (reads .env on startup)
cd backend && python main.py
```

The thread pool queue is in-memory — restarting clears all pending/failed tasks, so you must resubmit.

### 5. Verify One Task Before Batch

Submit a single task and check its status before firing the full batch:

```bash
curl -X POST http://localhost:8483/api/generate_note \
  -H "Content-Type: application/json" \
  -d '{"video_url": "...", "platform": "bilibili", "quality": "fast", "model_name": "deepseek-chat", "provider_id": "deepseek", "style": "detailed"}'

# Wait 30s then check
sleep 30
curl http://localhost:8483/api/task_status/<task_id>
```

### 6. Submit Batch

```bash
while IFS= read -r url; do
  [ -z "$url" ] && continue
  curl -s -X POST http://localhost:8483/api/generate_note \
    -H "Content-Type: application/json" \
    -d "{\"video_url\": \"$url\", \"platform\": \"bilibili\", \"quality\": \"fast\", \"model_name\": \"MODEL\", \"provider_id\": \"PROVIDER\", \"style\": \"STYLE\"}"
  echo ""
done < urls.txt
```

**Watch out**: Each `curl` call is a separate process — ~1-2s per task. For 82 tasks, expect ~2-3 minutes just for submission. If the command times out (default 5min), resume from the remaining lines with `tail -n +<line>`.

## Common Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| `ffprobe and ffmpeg not found` | No FFmpeg in PATH or .env | Set `FFMPEG_BIN_PATH` in `.env`, restart backend |
| `API Key 未配置` | Provider key not set or lost on restart | Re-run `update_provider` API |
| `pkg_resources` ModuleNotFoundError | setuptools >= 70 removed it | `pip install 'setuptools<70'` |
| `No module named 'yt_dlp'` | Dependencies not installed | `pip install -r requirements.txt` |
| Port 8483 already in use | Backend from previous session still running | Kill with `taskkill` |
| SSL errors on pip install | Network/proxy issue | Use Tsinghua mirror `-i https://pypi.tuna.tsinghua.edu.cn/simple` |

## Task Lifecycle

1. **Submit** → returns `task_id` immediately
2. **Status file** appears at `backend/note_results/{task_id}.status.json` — shows `PENDING` → `RUNNING` → `SUCCESS` or `FAILED`
3. **Output** lands as:
   - `backend/note_results/{task_id}_markdown.md` — the generated note
   - `backend/note_results/{task_id}.json` — full data
   - `backend/note_results/{task_id}_transcript.json` — raw transcript

## API Reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/generate_note` | POST | Submit a note generation task |
| `/api/task_status/{task_id}` | GET | Check task status/result |
| `/api/update_provider` | POST | Set provider API key |
| `/api/model_list/{provider_id}` | GET | List models for a provider |
| `/api/get_all_providers` | GET | List all configured providers |

## Request Payload for `/api/generate_note`

```json
{
  "video_url": "https://www.bilibili.com/video/BVxxx",
  "platform": "bilibili",
  "quality": "fast",
  "model_name": "deepseek-chat",
  "provider_id": "deepseek",
  "style": "detailed",
  "format": [],
  "screenshot": false,
  "link": false
}
```

## Dependencies

- **Python 3.11+** with `requirements.txt` installed
- **FFmpeg** (with `FFMPEG_BIN_PATH` in `.env` or system PATH)
- **API key** configured via `/api/update_provider` (stored in SQLite, persists across restarts)
- Backend runs on **port 8483**, processes **3 tasks concurrently** (ThreadPoolExecutor, configurable via `TASK_MAX_WORKERS`)
