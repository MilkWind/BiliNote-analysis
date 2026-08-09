# BiliNote Analysis — Q&A Record

*Survey date: 2026-08-09*

---

## Q1: How does this project implement speech transcription and multimodal video understanding?

### Speech Transcription

Five engines implement a common `Transcriber` base class (`backend/app/transcriber/base.py`) with contract `transcript(file_path) -> TranscriptResult`.

| Engine | Type | Backend |
|---|---|---|
| Faster Whisper | Local | CTranslate2 Whisper from HuggingFace |
| MLX Whisper | Local | Apple MLX Whisper (macOS only) |
| Bcut | Online, free | Bilibili internal Jianying API |
| Kuaishou | Online, free | Kuaishou AI subtitle API |
| Groq | Online, API key | Groq OpenAI-compatible Whisper endpoint |

**Factory**: `transcriber_provider.py` — singleton cache keyed by `TranscriberType` enum, lazy instantiation. Generic entry point `get_transcriber(type, model_size, device)`.

**Unified output**: `TranscriptResult(language, full_text, segments: [TranscriptSegment])`.

**Pipeline**: check transcript cache → try platform subtitles → fallback to audio download + `transcriber.transcript(audio_file)`.

**Config**: `TranscriberConfigManager` persists engine type + model size to `config/transcriber.json`. Frontend settings page at `transcriber.tsx` supports engine selection, model download with progress polling, and custom model registration.

### Multimodal Video Understanding

Two mechanisms:

**Mechanism A (vision LLM)**: `video_understanding=True`
1. `VideoReader` extracts frames at `video_interval` seconds via ffmpeg (parallel, 8 workers)
2. MD5 deduplication removes adjacent identical frames
3. Frames grouped into grids (`grid_size`, e.g. 3×3), each cell resized to 960×540, timestamp overlay drawn
4. Grids base64-encoded → sent as `image_url` alongside transcript to vision LLM (GPT-4V/4o/etc.)
5. LLM sees the video content, inserts `*Screenshot-[mm:ss]` markers
6. Post-processing: ffmpeg extracts single frames at marked timestamps → `![](/static/screenshots/...)`

**Mechanism B (text-only)**: `screenshot=True` without `video_understanding` — LLM guesses screenshot positions from transcript text alone, no images sent.

**Convergence**: Both transcript text and base64 grid images are packed into a multimodal message in `UniversalGPT.create_messages()`, using OpenAI's `[{type: "text"}, {type: "image_url"}]` array format. Falls back to plain string for non-vision models.

---

## Q2: Does the application have note storage and RAG knowledge search?

### Note Storage

**Filesystem (primary)**: `note_results/{task_id}.json` contains full `NoteResult` — markdown, transcript (time-aligned segments), audio metadata (title, duration, cover URL, platform, video ID, raw yt-dlp info).

**SQLite** (`bili_note.db`): `video_tasks` table stores `video_id + platform → task_id` mapping for deduplication. `providers` and `models` tables store LLM configuration.

**Frontend**: Zustand task store persisted to IndexedDB. `NoteHistory` sidebar with fuzzy search (Fuse.js + pinyin matching). `MarkdownViewer` supports mind map, transcript view, version history, copy, download.

### RAG Knowledge Search

| Component | Implementation |
|---|---|
| Vector DB | ChromaDB (persistent, `vector_db/`) |
| Embedding | `all-MiniLM-L6-v2` (~80MB, downloads on first use) |
| Chunking | 3 types: heading-split markdown, sliding-window transcript (15 segments, 3 overlap), single metadata blob |
| Retrieval | Fixed quota: 1 meta + 2 markdown + 3 transcript chunks per query |
| LLM | Any OpenAI-compatible provider |
| Tool calling | 3 tools: `lookup_transcript`, `get_video_info`, `get_note_content` — up to 3 rounds |

**Flow**: question → vector retrieval (6 chunks) → system prompt with context + tool definitions → LLM can call tools to fetch full transcript/metadata → final answer with source citations.

**UI**: `ChatPanel` with Ant Design X bubbles, Markdown rendering, collapsible source citations. Indexing auto-triggers after note generation; polls every 2s while downloading embedding model.

---

## Q3: Does it support classifying notes by different domain knowledge?

**No.** The note history is a flat list with only fuzzy title search. The `Task` interface has no fields for category, tags, domain, or folder. There is no classification API, no automatic domain tagging via LLM, and no folder/collection grouping in the UI.

The app is designed as a per-video note generator with searchable history, not a knowledge management system with domain-based organization.

---

## Q4: Does it integrate multiple video receive approaches?

**Yes, five input channels across two surfaces:**

### Web Frontend
1. **URL paste** — user selects platform from dropdown, pastes video URL
2. **Local file upload** — drag-and-drop or file picker for local videos

### Browser Extension
3. **Floating action button** — pink "BiliNote" button appears on supported video pages
4. **Popup submission** — extension popup detects platform from active tab, exposes full settings
5. **Right-click context menu** — "用 BiliNote 总结此视频" on pages, links, or video elements

### Downloader Selection

Dictionary-based lookup `SUPPORT_PLATFORM_MAP[platform]` maps to one of five downloaders, all implementing `download()` / `download_video()` / `download_subtitles()`:

| Downloader | Audio Source | Subtitle Support |
|---|---|---|
| Bilibili | yt-dlp + cookie injection + anti-scraping patch | Bilibili API (wbi-signed) + yt-dlp fallback |
| YouTube | yt-dlp + proxy | `youtube-transcript-api` (manual > auto) |
| Douyin | Internal API (msToken + a_bogus anti-bot) | Not supported |
| Kuaishou | GraphQL API → ffmpeg mp4→mp3 | Not supported |
| Local | ffmpeg video→mp3 + cover extraction | Not supported |

**Extension bonus**: Bilibili subtitles can be pre-fetched in-browser using native login cookies, skipping backend download + transcription.

---

## Q5: Does it support resolution settings when downloading videos via URL?

**There is a quality parameter wired end-to-end, but it is non-functional.**

The data model defines three levels with intended audio bitrates:

| Level | Intended Bitrate | Actual Behavior |
|---|---|---|
| `fast` | 32 kbps | All downloaders ignore it |
| `medium` | 64 kbps | All downloaders ignore it |
| `slow` | 128 kbps | All downloaders ignore it |

The parameter flows from frontend form → API → `NoteGenerator._download_media()` → `downloader.download(quality=...)` but every downloader hardcodes its own settings (e.g., Bilibili hardcodes `preferredquality: '64'`, YouTube always uses `bestaudio`). The base class has a TODO comment acknowledging this: `#TODO 需要修改为可配置`.

---

## Q6: What does the "quality" concept mean across different downloaders?

The `quality` parameter is about **audio bitrate for transcription**, not video resolution for viewing. It's a speed-vs-accuracy tradeoff:

| Level | Bitrate | Tradeoff |
|---|---|---|
| `fast` | 32 kbps | Fastest download, lower transcription accuracy with background noise |
| `medium` | 64 kbps | Balanced |
| `slow` | 128 kbps | Best accuracy, slower download |

**Platform differences:**

- **Bilibili/YouTube (yt-dlp)**: Could meaningfully support quality selection — yt-dlp can pick between multiple audio formats at different bitrates. A proper implementation would change the format selector string and ffmpeg `preferredquality`.
- **Douyin**: Only one audio URL exists in the API response (`music.play_url.uri`). Quality selection is meaningless — you get what the platform serves.
- **Kuaishou**: Downloads the single mp4 from GraphQL, then ffmpeg extracts audio. Quality could control the mp3 encoder bitrate during conversion, but the source is already compressed.
- **Local**: User-provided files have fixed bitrate. Re-encoding at higher bitrate doesn't recover lost quality.

---

## Q7: How can multimodal video understanding work without resolution settings? Don't vision LLMs care about resolution?

**Resolution matters for vision LLMs, but in the opposite direction — higher resolution is often harmful for this use case.**

### What the Pipeline Actually Does

Frames are extracted at native video resolution, then resized to **960×540** per cell (PIL LANCZOS), assembled into grids, JPEG-encoded at quality 90, and sent with `detail: "auto"`.

### Why Fixed 960×540 Is Reasonable

**Token cost dominates.** OpenAI vision pricing in high detail mode tiles images into 512×512 chunks (170 tokens each + 85 base). A 2880×1620 grid in high detail → ~2,125 tokens per grid. A 30-minute video at 6s intervals → 300 frames → 33 grids → ~70,000 vision tokens. At `detail: "auto"`, the model can choose low detail (85 tokens fixed) for simple scenes.

**The task doesn't need high resolution.** The LLM is doing scene-level understanding ("what's happening at this moment"), not OCR on fine text. The overlaid mm:ss timestamps are drawn at 48px font. 540p is adequate.

**What users CAN control is more impactful:**
- `video_interval` (1–30s): temporal density — more frames = more visual context but more grids/tokens
- `grid_size` (1×1 to 10×10): frames per grid — larger grids = fewer API calls but less detail per cell

These knobs control cost/quality more than resolution would, and they're exposed in the UI because they're easier to reason about.

---

## Q8: Does the application support note export? What export formats are available?

**Partially.** The only functional exports are client-side in the browser.

### Actually Working (Frontend, Browser-Side)

| Format | Implementation | Where |
|---|---|---|
| **Markdown (.md)** | Creates a `Blob` from rendered markdown content, triggers browser download | `MarkdownViewer.tsx`, "导出 Markdown" button |
| **Mind map SVG (.svg)** | Serializes the Markmap SVG DOM via `XMLSerializer`, downloads as `.svg` | `MarkmapComponent.tsx`, export button in mind map view |

Both are pure client-side — no backend round-trip.

### Partially Implemented (Backend, Not Wired Up)

`backend/app/utils/export.py` — `ExportUtils` class declares support for four formats:

| Format | Method | Status |
|---|---|---|
| **PDF** | `_to_pdf()` | **Implemented** — uses `markdown-pdf` library, embeds images as base64 (converts `/static/screenshots/` paths to inline data URIs), saves to `data/note_output/` |
| **HTML** | `_to_html()` | **Stub** — called but method body doesn't exist |
| **Word (.docx)** | `_to_word()` | **Stub** — called but method body doesn't exist |
| **PNG image** | `_to_image()` | **Stub** — called but method body doesn't exist |

However, **none of these backend exports are accessible to users** because there is no export API endpoint in any router, nothing imports `ExportUtils`, and the frontend has no export format selector or backend export calls.

---

## Q9: How many LLM providers can I choose for video understanding?

**3 out of 7 built-in providers support vision, plus any custom OpenAI-compatible vision API you add.**

### 7 Built-in Providers

| Provider | Base URL | Has Vision? |
|---|---|---|
| **OpenAI** | `api.openai.com/v1` | Yes — GPT-4V, GPT-4o, GPT-4.1 |
| **DeepSeek** | `api.deepseek.com` | No — text-only (confirmed by issue #282) |
| **Qwen** | `dashscope.aliyuncs.com/compatible-mode/v1` | Yes — Qwen-VL models via compatible endpoint |
| **Gemini** | `generativelanguage.googleapis.com/v1beta/openai/` | Yes — Gemini Flash/Pro via OpenAI-compatible endpoint |
| **Groq** | `api.groq.com/openai/v1` | No — specializes in fast text inference |
| **Ollama** | `127.0.0.1:11434/v1` | Depends on model — llama3.2-vision etc. may work |
| **Claude** | `https://` (incomplete URL) | Not functional — URL is a placeholder |

### Custom Providers

Users can add any custom provider via `POST /add_provider` with their own `api_key` + `base_url`. Since all providers go through `GPTFactory.from_config()` → `OpenAICompatibleProvider` → `UniversalGPT`, any OpenAI-compatible vision API endpoint works.

### How It Actually Works

All providers route through `UniversalGPT.create_messages()`. When `video_understanding=true` and `video_img_urls` is populated, it builds the OpenAI multimodal content array format. When empty, it falls back to plain string. There is **no provider-level gate** that checks vision capability before sending images — if you enable video understanding with a text-only model, the API call will fail with a provider error.

**Practical answer**: For video understanding, you need OpenAI, Gemini, Qwen (VL models), or a custom OpenAI-compatible vision API. That's 3 usable out of 7 built-in providers.

---

## Q10: I'm using Windows without GPU and want to use domestic APIs — are Bcut and Kuaishou recommended?

**Neither is a good long-term choice.** Both rely on undocumented internal APIs that could break without warning.

### Bcut (Bilibili Jianying API)

- **Pros**: Free, no API key, decent Chinese speech accuracy (it powers 必剪/Jianying)
- **Cons**: Slow (chunked upload + up to 500s polling), fragile (undocumented internal API), audio sent to Bilibili's servers

### Kuaishou AI API

- **Pros**: Free, no API key, fast (single synchronous request, no polling), simplest implementation
- **Cons**: Always returns `language="zh"` (no real detection), undocumented internal API with same reliability risk, accuracy may vary for non-Kuaishou-style content

### Better Alternatives for Windows + Domestic

1. **Groq** — if accessible from China (may need proxy). Proper documented API, `verbose_json` with word-level timestamps, very fast (Groq LPU hardware), generous free tier.

2. **Faster Whisper on CPU** — `tiny` or `base` model runs on CPU with `int8` quantization. A 5-minute video takes ~2–3 minutes on a modern CPU. Private and reliable.

3. **Qwen/DashScope** — Alibaba's DashScope offers a documented Chinese speech recognition API (SenseVoice/Paraformer), and Qwen is already a built-in provider.

**Verdict**: Use Bcut or Kuaishou as a short-term convenience while setting up Groq or local Faster Whisper. Between the two, Bcut has better accuracy but is slower; Kuaishou is simpler and faster but accuracy varies.

---

## Q11: Do audio recognition and video understanding work in parallel, or is multimodal LLM alone sufficient?

**They are strictly sequential, not parallel.** Audio transcription must complete before the multimodal LLM is invoked. Multimodal LLM alone is NOT sufficient — the transcript is mandatory input.

### The Pipeline Order

```
Step 1: Get transcript
  → cache → platform subtitles → audio download + Whisper transcription

Step 2: Download media
  → If video_understanding=True: also download full video + extract frames + build grids
  → (audio + video frames happen in the same _download_media() call)

Step 3: GPT summarization
  → GPTSource(text=transcript.full_text, video_img_urls=[...])
  → gpt.summarize(source) — BOTH text and images sent to the LLM together
```

### Why Sequential, Not Parallel

**Data dependency** — the transcript text is the primary input to the LLM. The grid images are supplementary context. The code always includes transcript segments in `GPTSource`; `video_img_urls` is optional. The LLM correlates visual frames with transcript segments using overlaid timestamps — without the transcript, it has nothing to correlate against.

**Audio + video are already colocated** — when `video_understanding=True`, `_download_media()` downloads both audio and video together. Frame extraction happens right after audio extraction in the same step, so there's no wasted wall-clock time.

### What the Multimodal LLM Actually Does

The LLM doesn't "watch the video" independently. It receives both the full transcript text (accurate, from Whisper/subtitles) and timestamped grid thumbnails, then identifies visually significant moments to insert `*Screenshot-[mm:ss]` markers. The transcript carries the semantic content; the images help the LLM pick which frames are worth showing.

---

## Q12: Can I use non-matching platform APIs for transcription? (e.g., transcribe Bilibili videos with Kuaishou API)

**Yes, the transcription engine and video platform are fully decoupled.**

### How the Decoupling Works

Two independent selections in the pipeline:

- **Downloader** — chosen by video platform URL (bilibili → `BilibiliDownloader`). Handles audio extraction and metadata.
- **Transcriber** — chosen by user configuration in Settings. Receives a raw audio file path with no knowledge of its source.

The connection is just a file path:

```python
transcript = self.transcriber.transcript(file_path=audio_file)
# audio_file is just an .mp3 on disk, regardless of platform
```

### All Combinations Work

| Video Source | Transcriber | Works? |
|---|---|---|
| Bilibili video | Kuaishou API | Yes — Bilibili audio extracted, sent to Kuaishou API |
| YouTube video | Bcut API | Yes — YouTube audio extracted, sent to Bilibili's API |
| Kuaishou video | Groq API | Yes — Kuaishou audio extracted, sent to Groq |
| Douyin video | Faster Whisper (local) | Yes — Douyin audio extracted, transcribed locally |
| Local file | Bcut API | Yes — any audio sent to Bilibili's API |

### Caveats

- Bcut and Kuaishou APIs are tuned for **Chinese speech** — using them on English YouTube videos gives poor results
- Groq is **language-agnostic** (standard Whisper model)
- Kuaishou always returns `language="zh"` regardless of actual audio content
- If the platform has native subtitles (Bilibili, YouTube), those are used first and the transcriber is never called — this is a platform-subtitle preference, not a coupling constraint

---

## Q13: How many points of using this application need payment?

**The application itself costs nothing.** It is open source (MIT), self-hosted, uses SQLite and ChromaDB locally, and has no subscription, license key, or built-in payment system.

Every cost comes from **external API services you choose to connect**. There are three cost points:

### Cost Point 1: LLM for Note Generation (mandatory)

Every note generation calls the LLM API. Cost varies dramatically by provider and settings:

| Factor | Impact |
|---|---|
| **Provider/model** | OpenAI GPT-4o ~$2.5–10/1M input tokens; DeepSeek ~$0.14/1M; Qwen ~$0.5–2/1M; Gemini Flash ~$0.075/1M; Ollama **free** (local) |
| **Transcript length** | A 30-minute Chinese video produces ~5,000–8,000 tokens of transcript text |
| **video_understanding=true** | Adds vision tokens. With `detail: auto`, each grid image costs 85–2,000+ tokens depending on detail mode. A 30-min video at 6s intervals → ~33 grids → 2,800–70,000 vision tokens |
| **Chunking** | Very long transcripts split into multiple API calls by `RequestChunker` — each chunk = one paid request |
| **Merge step** | After chunking, a final merge call combines partial results — one extra API call |

**Rough estimate per 30-min video (text only)**: $0.01–0.05 with DeepSeek, $0.10–0.50 with GPT-4o. With video understanding enabled, multiply by 2–10× depending on `detail` mode and grid count.

### Cost Point 2: LLM for RAG Chat (optional, per question)

Each chat Q&A round sends 6 retrieved chunks + system prompt + up to 3 tool-calling rounds. Much smaller context than note generation — typically 500–2,000 tokens per question. Negligible cost with cheap providers (< $0.001/question); ~$0.01–0.05 with GPT-4o.

### Cost Point 3: Transcription API (optional — free alternatives exist)

| Engine | Cost |
|---|---|
| **Groq** | Has a free tier; paid tier charges per audio minute (~$0.002–0.01/min for Whisper) |
| **Bcut** | **Free** (undocumented internal Bilibili API) |
| **Kuaishou** | **Free** (undocumented internal Kuaishou API) |
| **Faster Whisper** | **Free** (local, uses your CPU/GPU) |
| **MLX Whisper** | **Free** (local, macOS only) |

A 30-minute video transcribed via Groq: ~$0.06–0.30. Via local Whisper or Bcut/Kuaishou: $0.

### What's Always Free

| Component | Cost |
|---|---|
| Application itself | $0 (open source) |
| Video/audio downloading (yt-dlp) | $0 |
| ChromaDB embedding (`all-MiniLM-L6-v2`) | $0 (local ONNX model, ~80MB download) |
| SQLite database | $0 (local file) |
| Frame extraction (ffmpeg) | $0 (local processing) |
| Mind map rendering (Markmap) | $0 (client-side) |
| Markdown/SVG export | $0 (client-side) |

### Cheapest Path

Use **Ollama** for LLM (local model) + **Faster Whisper tiny** for transcription (local, CPU) + skip video understanding. Everything runs on your machine with no external API calls. Tradeoff: local models are slower and less capable than cloud APIs.

### Most Expensive Path

OpenAI GPT-4o + video understanding at 2s intervals with 2×2 grids + Groq transcription for a 2-hour video: could reach **$2–5 in a single generation** due to high vision token consumption from dense frame sampling.
