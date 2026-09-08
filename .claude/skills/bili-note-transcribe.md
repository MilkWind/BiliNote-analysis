---
name: bili-note-transcribe
description: Batch transcribe Bilibili videos to manuscripts only (no AI notes) — choose transcriber engine (volc-seedasr / bcut / kuaishou / groq / fast-whisper), download audio, transcribe, and write readable Markdown manuscripts into backend/note_results.
---

# BiliNote Transcript-Only Batch

Generates **raw transcripts only** for a list of Bilibili videos and stores them as Markdown manuscripts — **no GPT/notes step, no provider/model selection, no `screenshot`/`link`/`video_understanding`**.

This is the deliberate offline counterpart of `bili-note-batch` (which always runs the full note pipeline through `POST /api/generate_note`). Transcript-only cannot be done through the notes endpoint, so it runs standalone Python workers under `backend/script/`.

Pipeline per video:
1. Download audio → `backend/download_audios/{BV}.mp3`
2. Transcribe with the chosen engine
3. Write manuscript → `backend/note_results/{视频标题}.md`

## Pre-condition

Run scripts **from `backend/`** with the venv python: `backend/.venv/Scripts/python.exe`. The backend server does **not** need to be running (the workers call `app/*` directly), but it usually is — that's fine, don't start a second copy.

Required for Bilibili:
- **Cookie** in `backend/config/downloader.json` (`bilibili.cookie`, must contain `SESSDATA`). Workers read it via `BilibiliDownloader`/`CookieConfigManager`. Without it yt-dlp fails with HTTP 412.
  ```bash
  curl -s http://localhost:8483/api/get_downloader_cookie/bilibili | python -c "import sys,json; d=json.load(sys.stdin); print('SET' if d.get('data') and d['data'].get('cookie') else 'MISSING')"
  ```
- **FFmpeg/ffprobe on PATH** (or `FFMPEG_BIN_PATH` in `.env`) — yt-dlp uses it to extract mp3.
- Engine key if needed (see Phase 1).

## Phase 1 — Choose Transcriber Engine

Ask the user which engine to use. Transcript-only workers instantiate the app's transcriber classes directly (`app/transcriber/*`), so the engine choice is per-run, not a global setting — no API/config switch needed.

| Engine | Transcriber class (`backend/app/transcriber/`) | Key / model | Transcribe concurrency | Semantics |
|---|---|---|---|---|
| `volc-seedasr` | `VolcSeedAsrTranscriber` | `VOLC_SEEDASR_API_KEY` (+ optional `VOLC_SEEDASR_RESOURCE_ID`) in repo-root `.env` | 4 | async submit/query; ~1s per min of audio after submit |
| `bcut` | `BcutTranscriber` | none | 3 | async upload/task/poll; circuit-break on 412/429; **must use a fresh instance per file** (upload session state is not thread-safe) |
| `kuaishou` | `KuaishouTranscriber` | none | 2–3 | single-shot per file |
| `groq` | `GroqTranscriber` | `groq` provider row (api_key) in `bili_note.db` | 4–8 | sync call; auto-compresses >18MB files |
| `fast-whisper` | `whisper.py` (`fast-whisper`) | local model must be downloaded | 1–2 | local; watch OOM |
| `mlx-whisper` | `mlx_whisper_transcriber.py` | local | 1 | macOS only |

Caveats:
- `volc-seedasr`: if `VOLC_SEEDASR_API_KEY` is missing from `.env`, fails with `VOLC_SEEDASR_API_KEY 未配置`. Error `45000030 requested resource not granted` means the Volcano console hasn't activated 大模型录音文件识别.
- `groq`: needs a `groq` provider row with a key in the DB (see `bili-note-init`).
- `fast-whisper`: model must exist (download via `POST /api/transcriber_download` or the frontend settings page) before the first run.
- Uploads are pace-limited to avoid `412`/`429`; never raise concurrency above the table without strong reason.

## Phase 2 — Prepare the Video List

Sources (as in `bili-note-batch`):
- `goal_videos/*.txt` — the common one
- `urls.txt`

Acceptable row formats:
1. Full URL per line: `https://www.bilibili.com/video/BVxxx`
2. `BV<id>\t标题` (title comes from an extracted card list — e.g. a saved HTML page). Use this when the manuscript filename must carry the video's real title.

```bash
grep -c 'http' goal_videos/<name>.txt        # sanity: URL rows
python -c "import re;print(sum(1 for l in open('goal_videos/<name>.txt',encoding='utf-8') if re.fullmatch(r'BV[0-9A-Za-z]{10}.*',l.strip())))"
```

When the file only has URLs and a real `{标题}.md` name is wanted, the worker should use `AudioDownloadResult.title` (fetched by yt-dlp) instead of the row text.

## Phase 3 — Pick / Write the Worker Script

One reference implementation already exists for **volc-seedasr**: `backend/script/transcribe_volc_batch.py`. It is the template for every engine:

- Input: rows from `goal_videos/*.txt`; `--limit N` for smoke tests.
- Reads cookie from `backend/config/downloader.json` via `BilibiliDownloader`, audio to `backend/download_audios/{BV}.mp3` (skips existing → resume-safe).
- Transcriber concurrency `TR_WORKERS`, download concurrency `DL_WORKERS=2` with a start-pacer (`DL_PACE`) to keep Bilibili downloads below the 412 threshold.
- Writes manuscript `backend/note_results/{标题}.md` (filename sanitized for Windows) with shape:

  ```markdown
  # {视频标题}

  > 视频地址：https://www.bilibili.com/video/{BV}
  > 转写时间：<iso>

  ## 转写文稿

  {transcript text, paragraphized on Chinese sentence-final punctuation}
  ```

- Transcript **text** is derived from `TranscriptResult.segments` (drop `start/end`, paragraphize). Skip the video if its manuscript already exists.
- Bookmarks: `backend/transcribe_volc_state.json` (per-BV ok/err) and `backend/transcribe_volc_failed.txt` (BV per line).

For another engine: copy `transcribe_volc_batch.py`, then change only:
- the transcriber import + instantiation (keep a fresh instance per task for `bcut`; for `bcut` reuse `transcribe_bcut.py`'s upload/poll primitives + circuit breaker instead of `transcript()`),
- `TR_WORKERS` / pacing per the Phase 1 table,
- the manuscript writer stays identical.

Sanitize titles before writing: strip `\ / : * ? " < > |` (Windows-illegal) and a trailing dot; these titles also commonly contain `！？【】#` which are safe.

## Phase 4 — Verify One Video First

```bash
cd backend
.venv/Scripts/python.exe script/transcribe_volc_batch.py --limit 1 2>&1
```

Wait for `[done] dl_ok=1 ... tr_ok=1 tr_err=0`, then confirm the manuscript exists and reads correctly:
```bash
ls -la note_results/*.md
head -n 20 note_results/*.md
```

If it fails, fix before the full run (see Common Failure Modes).

## Phase 5 — Run the Batch

```bash
cd backend
.venv/Scripts/python.exe script/transcribe_volc_batch.py 2>&1 | tee transcribe_volc.log
```

Long job → run in background and poll (PowerShell):
```powershell
Start-Process -FilePath ".venv\Scripts\python.exe" `
  -ArgumentList "script\transcribe_volc_batch.py" `
  -WorkingDirectory "D:\...\backend" `
  -RedirectStandardOutput transcribe_volc.log -RedirectStandardError transcribe_volc.log.err
```

Interrupted? Just rerun — already-downloaded mp3s and already-written manuscripts are skipped, failed BVs are picked up again.

## Phase 6 — Monitor

```bash
cd backend
ls note_results/*.md | wc -l                     # manuscripts written
tail -n 5 transcribe_volc.log.err                # [tr-OK]/[tr-FAIL]/[done] lines
cat transcribe_volc_state.json | python -c "import sys,json;d=json.load(sys.stdin);print('ok:',sum(1 for v in d.values() if v.get('ok')),'err:',sum(1 for v in d.values() if not v.get('ok')))"
cat transcribe_volc_failed.txt                   # BVs that failed (rerun to retry)
```

The run ends when the log shows `[done]`. Do **not** generate notes from these manuscripts automatically — transcript-only is the deliverable. Subsequent note generation (if wanted) is a separate `bili-note-batch` run.

## Common Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| `HTTP 412` during download | Bilibili needs auth / rate-limited | Cookie with `SESSDATA` set; lower `DL_WORKERS`, raise `DL_PACE` |
| `VOLC_SEEDASR_API_KEY 未配置` | key missing | Add to repo-root `.env` |
| `45000030 requested resource not granted` | Volcano resource not activated | Enable 大模型录音文件识别 in Volcano console |
| `Groq 供应商未配置` | no groq provider row/key in DB | Configure via `bili-note-init` |
| bcut task `state=3` / poll fails | ASR task failed | Script retries whole file with 60/120s backoff; rerun log for stragglers |
| bcut cross-file corruption when parallelized | shared upload session state | Fresh `BcutTranscriber()` per task (as in `transcribe_bcut.py`) |
| fast-whisper model not ready | model not downloaded | `POST /api/transcriber_download`, or switch engine |
| Manuscript bytes look garbled | console codepage, not the file | Read the `.md` with a UTF-8 tool, not PowerShell `Get-Content` |

## Related

- `bili-note-batch` — full note generation (needs provider/model/style/format).
- `bili-note-init` — `.env`, backend start, provider keys, local model download.
