# BiliNote Batch Processing Guide

Two flows: init (one-time backend setup) and batch (repeatable video processing).

Companion Claude skills: `bili-note-init` and `bili-note-batch`.

---

## Flow 1: Init — Backend Startup

### 1.1 Create `.env` with FFmpeg Path

Copy `.env.example` → `.env` and set `FFMPEG_BIN_PATH`:

```
FFMPEG_BIN_PATH=D:/media-tools/ffmpeg-2026-08-06-git-essentials_build/bin
```

Confirm `backend/main.py` calls `ensure_ffmpeg_or_raise()` in the lifespan. If missing, ffmpeg won't be added to PATH and yt-dlp will fail.

Find ffmpeg:
```bash
which ffmpeg
# or: ls /d/media-tools/ffmpeg*/bin/ffmpeg.exe
```

### 1.2 Start Backend

Use a venv (recommended):

```bash
cd backend

# One-time setup (fresh clone):
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt

# Start (port 8483)
.venv/Scripts/python.exe main.py
```

Or without venv:
```bash
cd backend
pip install -r requirements.txt
python main.py
```

Use Python 3.11–3.13. Avoid 3.14.

Kill stale process if needed:
```bash
netstat -ano | grep 8483
taskkill //PID <pid> //F
```

### 1.3 Verify Backend is Running

```bash
curl -s -m 3 http://localhost:8483/api/get_all_providers | head -c 80
```

### 1.4 Configure API Key

```bash
curl -X POST http://localhost:8483/api/update_provider \
  -H "Content-Type: application/json" \
  -d '{"id": "deepseek", "api_key": "sk-xxx"}'

# Verify
curl -s http://localhost:8483/api/model_list/deepseek
```

Check all providers:
```bash
curl -s http://localhost:8483/api/get_all_providers | python -c "import sys,json; data=json.load(sys.stdin); [print(f'{p[\"id\"]}: key={\"SET\" if p.get(\"api_key\") else \"MISSING\"}') for p in data.get('data',[])]"
```

API keys persist in SQLite across restarts.

---

## Flow 2: Batch — Configure & Submit

### 2.1 Confirm 4 Things

#### a) 笔记风格 (style)

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

#### b) 笔记格式 (format) — multi-select

| Value | Label | Effect |
|---|---|---|
| `toc` | 目录 | TOC from `##` headings |
| `link` | 原片跳转 | `*Content-[mm:ss]` timestamps |
| `screenshot` | 原片截图 | `*Screenshot-[mm:ss]` markers |
| `summary` | AI总结 | `## AI 总结` section |

#### c) 供应商 & 模型 (provider & model)

```bash
# Providers and key status
curl -s http://localhost:8483/api/get_all_providers | python -c "import sys,json; d=json.load(sys.stdin); [print(f'{p[\"id\"]:12s} key={\"SET\" if p.get(\"api_key\") else \"MISSING\"}') for p in d.get('data',[])]"

# Models for a provider
curl -s http://localhost:8483/api/model_list/<provider_id> | python -c "import sys,json; [print(f'  - {m[\"id\"]}') for m in json.load(sys.stdin)['data']['models']]"
```

#### d) 视频理解模型 (video_understanding)

Default `false`. Ask: "是否启用视频理解模型？（不强求启用）"

If enabled, also set `video_interval` (default 30) and `grid_size` (e.g. `[4, 4]`).

### 2.2 Verify One Task

```bash
curl -X POST http://localhost:8483/api/generate_note \
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
  }'

sleep 30
curl -s http://localhost:8483/api/task_status/<task_id> | python -m json.tool
```

### 2.3 Submit Batch

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

~1-2s per task. Resume interrupted batches with `tail -n +<line> urls.txt`.

### 2.4 Monitor Progress

```bash
cd backend/note_results
echo "Success: $(grep -l '"status": "SUCCESS"' *.status.json 2>/dev/null | wc -l)"
echo "Failed:  $(grep -l '"status": "FAILED"' *.status.json 2>/dev/null | wc -l)"
echo "Running: $(grep -l '"status": "RUNNING"' *.status.json 2>/dev/null | wc -l)"
echo "Pending: $(grep -l '"status": "PENDING"' *.status.json 2>/dev/null | wc -l)"
```

**Git Bash garbles Chinese output. Read markdown files directly instead of relying on curl output.**

---

## Task Lifecycle

1. **Submit** → returns `task_id`
2. **Status file**: `backend/note_results/{task_id}.status.json` — `PENDING` → `RUNNING` → `SUCCESS` / `FAILED`
3. **Output**:
   - `{task_id}_markdown.md` — generated note
   - `{task_id}.json` — full data
   - `{task_id}_transcript.json` — raw transcript

---

## Request Payload Reference

```json
{
  "video_url": "https://www.bilibili.com/video/BVxxx",
  "platform": "bilibili",
  "quality": "fast",
  "model_name": "<model_from_provider>",
  "provider_id": "<provider_id>",
  "style": "detailed",
  "format": ["toc", "link", "summary"],
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

| Field | Type | Default | Notes |
|---|---|---|---|
| `quality` | string | — | `"fast"` or `"hd"` |
| `style` | string | `null` | One of the 9 style values |
| `format` | array | `[]` | Subset of `["toc", "link", "screenshot", "summary"]` |
| `screenshot` | bool | `false` | Legacy — prefer `"screenshot"` in format array |
| `link` | bool | `false` | Legacy — prefer `"link"` in format array |
| `video_understanding` | bool | `false` | Extract key frames for visual LLM input |
| `video_interval` | int | `0` | Seconds between frame captures |
| `grid_size` | array | `[]` | Thumbnail grid, e.g. `[4, 4]` |
| `task_id` | string | `null` | Set to retry a failed task |
| `prefetched_transcript` | object | `null` | Pre-fetched subtitle data |

---

## API Reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/generate_note` | POST | Submit a note generation task |
| `/api/task_status/{task_id}` | GET | Check task status/result |
| `/api/update_provider` | POST | Set provider API key |
| `/api/model_list/{provider_id}` | GET | List models for a provider |
| `/api/get_all_providers` | GET | List all configured providers |

---

## Common Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| `ffprobe and ffmpeg not found` | FFmpeg not in PATH | Set `FFMPEG_BIN_PATH` in `.env`, restart backend |
| `API Key 未配置` | Provider key not set | Run `update_provider` API |
| `pkg_resources` ModuleNotFoundError | setuptools >= 70 removed it | `pip install 'setuptools<70'` |
| `No module named 'yt_dlp'` | Dependencies not installed | `pip install -r requirements.txt` |
| Port 8483 already in use | Previous backend still running | `taskkill //PID <pid> //F` |
| SSL errors on pip install | Network/proxy issue | Use Tsinghua mirror `-i https://pypi.tuna.tsinghua.edu.cn/simple` |
| numpy build fails (Python 3.14+) | No pre-built wheels | Use Python 3.11–3.13 |

## Dependencies

- Python 3.11–3.13
- FFmpeg (with `FFMPEG_BIN_PATH` in `.env` or system PATH)
- API key via `/api/update_provider`
- Backend on port 8483, 3 concurrent tasks (`TASK_MAX_WORKERS`)
