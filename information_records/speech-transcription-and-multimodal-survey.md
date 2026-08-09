# BiliNote Analysis — Speech Transcription & Multimodal Video Understanding

*Survey date: 2026-08-09*

---

## 1. Speech Transcription System

### 1.1 Engine Architecture

Five transcription engines, all implementing a common `Transcriber` abstract base class (`backend/app/transcriber/base.py`) with a single contract: `transcript(file_path) -> TranscriptResult`.

| Engine | Type | File | Backend |
|---|---|---|---|
| **Faster Whisper** | Local | `whisper.py` | CTranslate2-accelerated Whisper models from HuggingFace |
| **MLX Whisper** | Local | `mlx_whisper_transcriber.py` | Apple MLX-optimized Whisper (macOS only) |
| **Bcut** | Online, free | `bcut.py` | Bilibili's internal Jianying transcription API |
| **Kuaishou** | Online, free | `kuaishou.py` | Kuaishou AI subtitle generation API |
| **Groq** | Online, API key | `groq.py` | Groq's OpenAI-compatible Whisper endpoint |

### 1.2 Base Class & Data Model

**Abstract base** (`backend/app/transcriber/base.py`):

```python
class Transcriber(ABC):
    @abstractmethod
    def transcript(self, file_path: str) -> TranscriptResult: ...
    def on_finish(self, video_path: str, result: TranscriptResult) -> None: ...
```

**Unified output** (`backend/app/models/transcriber_model.py`):

```python
TranscriptSegment(start: float, end: float, text: str)
TranscriptResult(language: str | None, full_text: str, segments: list[TranscriptSegment], raw: dict | None)
```

Every engine produces this identical structure regardless of its underlying API or library.

### 1.3 Factory Pattern

`backend/app/transcriber/transcriber_provider.py` — module-level factory:

- **`TranscriberType`** enum: `FAST_WHISPER`, `MLX_WHISPER`, `BCUT`, `KUAISHOU`, `GROQ`
- **Singleton cache** `_transcribers` dict keyed by `TranscriberType`, lazily instantiated on first use
- **Generic entry**: `get_transcriber(type, model_size, device)` resolves string → enum → cached instance, falls back to `FAST_WHISPER` on unknown type
- **Platform gate**: MLX Whisper imports only on `Darwin` (macOS); `MLX_WHISPER_AVAILABLE` flag set at import time

### 1.4 How Each Engine Works

#### Faster Whisper (Local)

1. `whisper_models.py` resolves model name → HF repo ID via three-tier lookup (custom > builtin > passthrough)
2. Creates `faster_whisper.WhisperModel(model, device, compute_type, download_root)`
3. `model.transcribe(file_path)` → segments generator + language info
4. CUDA auto-detection via `torch.cuda.is_available()`; falls back to CPU with `int8` quantization
5. Corrupted downloads auto-purged and retried

Built-in models: `tiny` through `large-v3-turbo` mapped to `Systran/faster-whisper-*` repos.

#### MLX Whisper (Local, macOS only)

1. `MLX_MODEL_MAP` resolves size → `mlx-community/whisper-*-mlx` repo IDs
2. Auto-downloads via `huggingface_hub.snapshot_download()` if `config.json` missing locally
3. `mlx_whisper.transcribe(file_path, path_or_hf_repo=repo_id)` → dict with segments

#### Bcut (Bilibili Online API)

Multi-step workflow against `member.bilibili.com`:
1. `_upload()` — POST `/resource/create` (model_id="8"), get chunked upload URLs
2. `__upload_part()` — PUT each binary chunk, collect ETags
3. `__commit_upload()` — POST `/resource/create/complete` with aggregated ETags, get `download_url`
4. `_create_task()` — POST `/task` with the download URL reference
5. `_query_result()` — polling loop GET `/task/result` (up to 500× at 1s intervals), state 4 = done

#### Kuaishou (Online API)

Simplest engine — single synchronous multipart POST to `ai.kuaishou.com/api/effects/subtitle_generate` with `typeId=1`. Returns result immediately (no polling). Language hardcoded to `"zh"`.

#### Groq (Online API Key)

1. Audio > 18 MB → auto-compress via ffmpeg to 64 kbps MP3
2. OpenAI-compatible client pointed at Groq's base URL
3. `client.audio.transcriptions.create(model=..., response_format="verbose_json")`
4. Returns structured segments + language from Whisper API

### 1.5 Model Resolution (Faster Whisper)

`backend/app/transcriber/whisper_models.py` — `WhisperModelRegistry` class:

- **Tier 1 — Custom**: user-registered name→HF repo/local path mappings in `config/whisper_models.json`
- **Tier 2 — Built-in**: `BUILTIN_WHISPER_MODELS` dict (tiny/base/small/medium/large-v1/v2/v3/v3-turbo)
- **Tier 3 — Passthrough**: any string containing `/` (HF repo_id format) or an existing directory path

CRUD for custom models exposed via API endpoints (`/whisper_models` GET/POST/DELETE).

### 1.6 Configuration Management

`backend/app/services/transcriber_config_manager.py`:
- Persists `{transcriber_type, whisper_model_size}` to `config/transcriber.json`
- Falls back to env vars `TRANSCRIBER_TYPE` (default `"fast-whisper"`) and `WHISPER_MODEL_SIZE` (default `"tiny"`)
- `is_model_ready()` — for local engines, checks `model.bin` (fast-whisper) or `config.json` (MLX) exists on disk; online engines always return ready

`backend/app/transcriber/model_download_state.py`:
- In-process tracking of `downloading` / `done` / `failed` per model key
- `status_row()` builds frontend-ready JSON with error messages

### 1.7 Data Flow in Note Generation

```
POST /generate_note
  → TranscriberConfigManager.is_model_ready()   [gate: reject if local model missing]
  → NoteGenerator.__init__()
    → get_transcriber(type, model_size, device)  [factory, lazy singleton]
  → NoteGenerator.generate():
    1. Check transcript cache (task_id_transcript.json)
    2. Try platform subtitles (downloader.download_subtitles())
    3. Fallback: download audio → transcriber.transcript(audio_file)
       → cache TranscriptResult to JSON
    4. Feed transcript segments to LLM for note generation
```

Key architectural decisions:
- **Lazy initialization**: transcriber created at `NoteGenerator` construction, not app startup
- **Hard readiness gate**: `/generate_note` explicitly rejects with `reason: "transcriber_model_not_ready"` before queuing
- **Fallback chain**: platform subtitles preferred over audio transcription
- **Cache-first**: transcripts cached by `task_id` for retry resilience

### 1.8 Frontend Components

| Component | File | Role |
|---|---|---|
| Settings page | `pages/SettingPage/transcriber.tsx` | Engine selector, model download/status, custom model CRUD |
| Service layer | `services/transcriber.ts` | TypeScript types + API client functions |
| Transcript viewer | `pages/HomePage/components/transcriptViewer.tsx` | Scrollable time-aligned segment list |
| Note form | `pages/HomePage/components/NoteForm.tsx` | Catches model-not-ready errors, redirects to settings |
| Onboarding | `pages/Onboarding/index.tsx` | Step 3: recommends online engines to skip local downloads |
| Task store | `store/taskStore/index.ts` | Zustand + IndexedDB; stores `Transcript` per task |
| Polling hook | `hooks/useTaskPolling.ts` | 3-second polling, extracts transcript + markdown on SUCCESS |

### 1.9 Backend API Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/transcriber_config` | Current config + available types + model sizes + MLX availability |
| POST | `/transcriber_config` | Update engine type + model size |
| GET | `/transcriber_models_status` | Download status for all whisper models |
| POST | `/transcriber_download` | Trigger background model download |
| GET | `/whisper_models` | List builtin + custom model mappings |
| POST | `/whisper_models` | Add custom model mapping |
| DELETE | `/whisper_models/{name}` | Remove custom model mapping |
| GET | `/sys_health` | System health including whisper model status |

### 1.10 Events System

Uses `blinker` library:
- **Signal**: `transcription_finished`
- **Handler**: `cleanup_temp_files` — deletes temp audio files by video ID
- Registered at app startup in `main.py` lifespan context

---

## 2. Multimodal Video Understanding

### 2.1 Two Mechanisms

**Mechanism A: Multimodal LLM Vision** (`video_understanding=True`)
Frames are extracted, assembled into timestamped grid thumbnails, base64-encoded, and sent as `image_url` content alongside transcript text to a vision-capable LLM. The LLM *sees* the video content.

**Mechanism B: Text-only Screenshot Hints** (`screenshot=True` without `video_understanding`)
The prompt asks the LLM to *guess* where screenshots would help based on transcript text alone. No images are sent to the LLM.

### 2.2 API Parameters

`POST /generate_note` accepts:
- `video_understanding: bool` — enable multimodal vision analysis
- `video_interval: int` — seconds between extracted frames (default 6)
- `grid_size: list[int]` — grid dimensions, e.g. `[3, 3]` for 3×3 = 9 frames per thumbnail
- `screenshot: bool` — enable the older text-only screenshot path

### 2.3 Full Multimodal Pipeline (Mechanism A)

```
1. NoteGenerator._download_media()
   → Downloads full video file (need_video = screenshot or video_understanding)

2. VideoReader.run()                          [backend/app/utils/video_reader.py]
   a. ffmpeg.probe() → video duration
   b. Extract frames at video_interval seconds
      → parallel ffmpeg -ss N -i video.mp4 -frames:v 1 (ThreadPoolExecutor, 8 workers)
      → Capped at 1000 frames max
   c. MD5 deduplication: discard adjacent identical frames (static shots)
   d. Group frames into batches of grid_size[0] × grid_size[1]
      (e.g., 3×3 = 9 frames per grid image)
   e. PIL assembly per batch:
      - Resize each cell to 960×540
      - Draw yellow MM:SS timestamp in top-left corner of each cell
      - Paste into a 2880×1620 grid image → save as grid_N.jpg
   f. Base64-encode each grid → data:image/jpeg;base64,...
   g. Return list of base64 data URIs → stored in self.video_img_urls

3. NoteGenerator._summarize_text()
   → GPTSource(text=transcript, video_img_urls=[...])
   → gpt.summarize(source)

4. UniversalGPT.summarize()                   [backend/app/gpt/universal_gpt.py]
   a. RequestChunker splits transcript into byte-budgeted chunks
   b. Grid images distributed proportionally across chunks
      (image i → chunk floor(i × chunk_count / total_images))
   c. create_messages() builds multimodal content array:
      [
        {"type": "text", "text": "<prompt + transcript segment>"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,...", "detail": "auto"}},
        ...
      ]
   d. Each chunk → client.chat.completions.create(model=..., messages=...)

5. LLM (GPT-4V / GPT-4o / Qwen-VL)
   → Reads timestamps from grid cell overlays
   → Cross-references visual content with transcript segments
   → Generates markdown with *Screenshot-[mm:ss] markers

6. Post-processing: _post_process_markdown()
   → Regex extract *Screenshot-[mm:ss] markers
   → ffmpeg extract exact frame at each timestamp
   → Save to static/screenshots/screenshot_XXX_UUID.jpg
   → Replace marker with ![](/static/screenshots/screenshot_XXX_UUID.jpg)
```

### 2.4 Key Design Decisions

**String vs. array content format** (`universal_gpt.py:create_messages()`):
- When `video_img_urls` is empty → content is a plain string (compatible with non-vision models)
- When `video_img_urls` has entries → content switches to OpenAI multimodal array format `[{type: "text"}, {type: "image_url"}]`
- This auto-detection avoids `invalid_request_error` on models that reject array content (e.g., older DeepSeek chat)

**Proportional image distribution** (`request_chunker.py`):
- Each grid image is assigned to the chunk whose index matches `(image_index × chunk_count) / total_images`
- If a chunk can't fit its assigned image within the byte budget, a new dedicated chunk is created
- Ensures balanced visual context across chunks

**Single-frame post-processing** (`video_helper.py:generate_screenshot()`):
- After the LLM returns markers, `ffmpeg -ss <timestamp> -i <video> -frames:v 1 -q:v 2` extracts exact frames
- The LLM sees compressed grid thumbnails at fixed intervals; post-processing extracts high-quality single frames at the exact timestamps the LLM chose

### 2.5 The Multimodal Prompt

From `backend/app/gpt/prompt_builder.py:get_screenshot_format()`:

```
你收到的截图一般是一个网格，网格的每张图片就是一个时间点，
左上角会包含时间mm:ss的格式，请你结合我发你的图片插入截图提示，
请你帮助用户更好的理解视频内容，请你认真的分析每个图片和对应的转写文案，
插入最合适的内容来备注用户理解，请一定按照这个格式返回否则系统无法解析：
- 格式：*Screenshot-[mm:ss]
```

Translation: the prompt instructs the LLM to inspect each grid cell (with its mm:ss overlay), correlate visuals with the transcript, and insert `*Screenshot-[mm:ss]` markers at the most relevant moments.

### 2.6 GPT Class Landscape

| Class | File | Multimodal? | Status |
|---|---|---|---|
| **UniversalGPT** | `universal_gpt.py` | **Yes** | Active — used by `GPTFactory.from_config()` |
| OpenaiGPT | `openai_gpt.py` | No | Legacy wrapper |
| DeepSeekGPT | `deepseek_gpt.py` | No | Legacy wrapper |
| QwenGPT | `qwen_gpt.py` | No | Legacy wrapper |

Only `UniversalGPT` (the factory path) supports multimodal input. All providers go through it.

### 2.7 Key Files Summary

| File | Role |
|---|---|
| `backend/app/routers/note.py` | API entry: accepts `video_understanding`, `video_interval`, `grid_size`, `screenshot` |
| `backend/app/services/note.py` | Orchestrator: download → extract frames → summarize → insert screenshots |
| `backend/app/utils/video_reader.py` | Frame extraction: ffmpeg probe/extract, MD5 dedup, PIL grid assembly, base64 encoding |
| `backend/app/utils/video_helper.py` | Single-frame ffmpeg extraction for post-processing |
| `backend/app/utils/screenshot_marker.py` | Regex: `\*?Screenshot-(?:\[(\d{2}):(\d{2})\]|(\d{2}):(\d{2}))` |
| `backend/app/gpt/universal_gpt.py` | Multimodal LLM client: builds OpenAI content array, handles checkpoint/resume, merges partials |
| `backend/app/gpt/request_chunker.py` | Splits transcript + images into byte-budgeted chunks, distributes images proportionally |
| `backend/app/gpt/prompt.py` | Prompt templates: `BASE_PROMPT`, `SCREENSHOT`, `LINK`, `AI_SUM`, `MERGE_PROMPT` |
| `backend/app/gpt/prompt_builder.py` | Dynamic prompt assembly: format selectors for screenshot, link, toc, summary, 9 note styles |
| `backend/app/gpt/gpt_factory.py` | Creates `UniversalGPT` from provider config (the only active GPT path) |
| `backend/app/models/gpt_model.py` | `GPTSource` dataclass with `video_img_urls: list[str] | None` |

---

## 3. How The Two Systems Converge

The transcription system produces structured text (`TranscriptResult` with time-aligned segments) from audio. The multimodal system produces visual context (timestamped grid thumbnails) from video frames.

They converge in `UniversalGPT.summarize()`, where both the transcript text and the base64-encoded grid images are packed into a single multimodal message sent to a vision-capable LLM. The LLM correlates visual frames with transcript segments using the mm:ss timestamps overlaid on each grid cell.

The final output is markdown notes containing:
- Text summaries derived from the transcript
- `*Screenshot-[mm:ss]` markers placed at visually significant moments (chosen by the LLM based on what it *saw*)
- After post-processing, these markers are replaced with actual image embeds pointing to high-quality single-frame screenshots
