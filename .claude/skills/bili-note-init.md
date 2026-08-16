---
name: bili-note-init
description: Initialize the BiliNote backend — asks for .env configs (FFmpeg path, transcriber type), starts backend, configures API keys.
---

# BiliNote Init — Backend Setup

## Pre-check — Python Version

```bash
python --version
```

Use Python 3.11–3.13. Python 3.14+ lacks pre-built wheels for numpy/ctranslate2.

## Phase 1 — Confirm .env Configurations

### 1. FFmpeg Path (FFMPEG_BIN_PATH)

Ask: "FFmpeg 安装在哪个目录？"

Search if unknown:
```bash
which ffmpeg
ls /d/media-tools/ffmpeg*/bin/ffmpeg.exe 2>/dev/null
```

Set to the `bin/` directory containing `ffmpeg.exe`: `D:/media-tools/ffmpeg-xxx/bin`. Leave empty if ffmpeg is in system PATH.

### 2. Transcriber Type (TRANSCRIBER_TYPE)

Ask: "用哪个转写引擎？"

| Value | Label | Notes |
|---|---|---|
| `bcut` | 必剪（Bilibili 内置） | No key or model download. Extracts Bilibili subtitles directly. |
| `fast-whisper` | Faster Whisper（本地） | Local model (~75MB tiny). Optional: `HF_ENDPOINT=https://hf-mirror.com` in `.env`. |
| `groq` | Groq（在线） | Cloud-based, needs Groq API key. |
| `kuaishou` | 快手 | For Kuaishou platform. |
| `volc-seedasr` | 火山引擎 SeedASR（在线） | Cloud ASR (submit/query, `volc.bigasr.auc`). Needs `VOLC_SEEDASR_API_KEY` in `.env`. Accepts local files as base64 — no public URL needed. |
| `mlx-whisper` | MLX Whisper | macOS only (Apple Silicon). |

Note: `volc-seedasr` uses resource `volc.bigasr.auc` by default (configurable via `VOLC_SEEDASR_RESOURCE_ID`). If the API returns `45000030 requested resource not granted`, the account hasn't activated that resource — check the Volcano Engine console 开通 status for 大模型录音文件识别.

### 3. LLM Provider API Key

Ask: "用哪个 LLM 供应商？需要提供 API key。"

Common: `deepseek`, `openai`, `qwen`, `Claude`, `gemini`, `groq`, `ollama`.

## Phase 2 — Create/Update .env

Copy `.env.example` → `.env`. Set:

```
FFMPEG_BIN_PATH=D:/media-tools/ffmpeg-xxx/bin
TRANSCRIBER_TYPE=bcut
BACKEND_PORT=8483
NOTE_OUTPUT_DIR=note_results
```

For `volc-seedasr`, add (get key from Volcano Engine console; also switch transcriber via Settings UI or `POST /api/transcriber_config` — `TRANSCRIBER_TYPE` is only the first-boot default):
```
VOLC_SEEDASR_API_KEY=<your-key>
```

For fast-whisper in China, optionally add:
```
HF_ENDPOINT=https://hf-mirror.com
```

## Phase 3 — Start Backend

Use a venv (recommended). If `backend/.venv` doesn't exist:

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
```

Start:
```bash
# Kill stale process
netstat -ano | grep 8483
# taskkill //PID <pid> //F   (if needed)

cd backend && .venv/Scripts/python.exe main.py
```

Verify:
```bash
sleep 5 && curl -s http://localhost:8483/api/get_all_providers | head -c 80
```

Run pip install and backend start in foreground.

## Phase 4 — Configure API Key

```bash
curl -X POST http://localhost:8483/api/update_provider \
  -H "Content-Type: application/json" \
  -d '{"id": "<provider_id>", "api_key": "sk-xxx"}'
```

Verify:
```bash
curl -s http://localhost:8483/api/get_all_providers | python -c "import sys,json; d=json.load(sys.stdin); [print(f'{p[\"id\"]}: key={\"SET\" if p.get(\"api_key\") else \"MISSING\"}') for p in d.get('data',[])]"
```

## Phase 5 — Download Model (fast-whisper only)

```bash
curl -X POST http://localhost:8483/api/transcriber_download \
  -H "Content-Type: application/json" \
  -d '{"model_size": "tiny", "transcriber_type": "fast-whisper"}'

curl -s http://localhost:8483/api/transcriber_models_status | python -m json.tool
```

Skip for `bcut`, `groq`, `kuaishou`, or `volc-seedasr`.

## Verification Checklist

- [ ] `.env` has `FFMPEG_BIN_PATH` and `TRANSCRIBER_TYPE`
- [ ] Backend running on port 8483
- [ ] API key configured for chosen provider
- [ ] (fast-whisper) Model downloaded
- [ ] (volc-seedasr) `VOLC_SEEDASR_API_KEY` set in `.env`
