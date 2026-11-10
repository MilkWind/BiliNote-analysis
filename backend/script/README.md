# backend/script — Script Index

Purpose: pick the right script quickly. Each entry says **what it does**, **when
to use it**, and **whether it is current or superseded**.

Run everything from `backend/` so the venv is used:

```bash
cd backend
.venv/Scripts/python.exe script/<name>.py --help
```

---

## 1. The full pipeline (start here)

The end-to-end flow for a new batch of UP sources:

```
build_goal_video_lists.py   ->  goal_videos/<UP>.txt
predownload_goal_media.py   ->  local media cache
batch_goal_notes_v2.py      ->  notes in backend/note_results/
copy_notes_to_kb_v2.py      ->  notes/<category>/<UP>/*.md
inject_source_links.py      ->  adds the > 来源链接 line
```

`run_full_plan.py` chains the first three unattended (phase 1 downloads, then
phase 2 parsing at higher concurrency).

### `run_full_plan.py` — **the one to use for a whole batch**
Two-phase unattended runner: pre-downloads all media with 2 workers, verifies it,
then starts a second backend on port 8484 and parses at `PHASE2_WORKERS` (default
32, **8 is the proven-safe value on this machine**). Supports `PAUSE_AT` for a
timed stop. Resume-safe: re-running skips finished media and finished notes.

```bash
PHASE2_WORKERS=8 python script/run_full_plan.py
PAUSE_AT="2026-11-07 05:00:00" python script/run_full_plan.py
```

### `batch_goal_notes_v2.py` — the submission driver (phase 2 alone)
Submits each URL to `/api/generate_note`, honours per-source style /
video-understanding / transcript settings, retries failures, dedupes against the
DB and the progress log. Use directly when media is already cached or when you
want fine control (`--only`, `--limit`, `--concurrency`, `--api-base`).
`--check` runs an Ark preflight before submitting anything.

```bash
python script/batch_goal_notes_v2.py --dry-run
python script/batch_goal_notes_v2.py --check
python script/batch_goal_notes_v2.py --api-base http://localhost:8484 --concurrency 8
```

### `predownload_goal_media.py` — media cache (phase 1 alone)
Downloads MP4 (only for video-understanding tasks) and MP3 + `.meta.json` for
every task into `backend/data/data/`. **Use `--workers 2`** — Bilibili throttles
concurrent downloads from one account (8 workers dropped to ~8 KiB/s). Has a
disk guard and a network circuit breaker.

```bash
python script/predownload_goal_media.py --workers 2
python script/predownload_goal_media.py --only 前端小码哥 --limit 5
```

### `batch_status_v2.py` — progress snapshot (read-only, safe any time)
Prints totals, in-flight count, and a per-source SUCCESS/FAILED breakdown from
`_goal_notes_progress_v2.jsonl`. Run this to answer "how far along is it?".

```bash
python script/batch_status_v2.py
```

---

## 2. Knowledge-base import

### `copy_notes_to_kb_v2.py` — **use this one**
Copies generated notes into `persional-knowledge/notes/<category>/<UP>/`.
Filenames come from `audio_meta.title` (most notes have no H1), multi-part titles
are reduced to the part name, rip tags (`-1080P 高清-AVC`) are stripped, Windows
illegal characters become fullwidth, collisions get ` (2)` suffixes. Idempotent
via `_kb_copy_state.json`; writes `_kb_copy_report.md`.
`--include-orphans` also picks up notes that finished but never got a progress
line (happens after a crash).

```bash
python script/copy_notes_to_kb_v2.py --dry-run
python script/copy_notes_to_kb_v2.py --include-orphans
```

To add a batch: edit the `TARGETS` table (source label -> folder). Unknown
sources are counted as `unmapped` and skipped, never guessed.

### `inject_source_links.py` — provenance header
Adds `> 来源链接：https://www.bilibili.com/video/BV…?p=N` to each imported note,
matching the existing KB style (below an H1, or first line when there is none).
Requires `copy_notes_to_kb_v2.py` to have run first (it reads the state file).
Idempotent; preserves CRLF.

```bash
python script/inject_source_links.py --dry-run
python script/inject_source_links.py
```

---

## 3. Gathering source lists (`pagination_query/`)

| Script | Use |
|---|---|
| `pagination_query/build_goal_video_lists.py` | **Current.** Builds `goal_videos/<UP>.txt` from a space or 合集 URL; supports date filters, exclusions, 分P expansion, and KB title dedupe (threshold 0.88). Writes `_dedupe_reports/`. |
| `pagination_query/fetch_space_videos.py` | Lower level: dump every video URL from one UP space. Handles WBI signing and the `dm_img_*` fingerprint. |
| `pagination_query/fetch_video_pages.py` | Fetch 分P titles for a list of BVs; dedupes titles. Useful for inspecting a 合集 before generating. |
| `pagination_query/classify_programmer_fangge.py` | One-off: classifies 程序员方格 分P into 17 topic buckets. Reference for any future categorization. |

Details and API notes: `pagination_query/lessons.md`.

---

## 4. Other transcription / download helper scripts

| Script | Use | Status |
|---|---|---|
| `transcribe_volc_batch.py` | Download audio + Volc SeedASR → plain Markdown manuscripts, no LLM. Hardcodes `goal_videos/血狼破军.txt`; change the constant for other lists. | Current |
| `transcribe_bcut.py` | Audio → bcut ASR → `transcription_files/{BV}.txt`, with rate-limit pacer. | Current |
| `download_audios.py` | Audio only into `download_audios/`, hardcoded to `渡一.txt`. | Legacy but usable |

---

## 5. Superseded — do not use for new work

Kept for reference only. **Several still point at paths that no longer exist**
(`document-projects`, or `persional-knowledge/technology/...` without `notes/`),
so they will fail if run as-is.

| Script | Superseded by | Note |
|---|---|---|
| `batch_goal_notes.py` | `batch_goal_notes_v2.py` | v1 driver, different manifest format. |
| `copy_notes_to_targets.py` | `copy_notes_to_kb_v2.py` | Needs the old `temp.txt` destination-column format. |
| `copy_notes_to_kb.py` | `copy_notes_to_kb_v2.py` | Stale target path, no CLI. |
| `attach_copy_rename.py` | `copy_notes_to_kb_v2.py` | Stale target (`document-projects`); adds headers though — see `inject_source_links.py` for that. |
| `copy_programmer_fangge_notes.py` | `copy_notes_to_kb_v2.py` | Specific to 程序员方格's category folders; already run. |
| `batch_programmer_fangge.py` | `batch_goal_notes_v2.py` | Specific to 程序员方格; already run. |
| `batch_submit.py` / `batch_bv_p.py` | `batch_goal_notes_v2.py` | Hardcode one input file; no per-source settings. |
| `check_complete_notes.py` | — | Stale KB path; rewrites notes in place via DeepSeek. Reference only. |
| `run_goal_notes.cmd` | `run_full_plan.py` | v1 Windows launcher. |
| `run_goal_notes_v2.cmd` | `run_full_plan.py` | Simple v2 launcher, kept for scheduled runs. |

---

## 6. Key data files (`goal_videos/`)

| File | Meaning |
|---|---|
| `temp.txt` | Human-written source list: `<label> <requirements> <URL>`. |
| `<UP>.txt` | One URL per line, `?p=N` for parts. Input to the drivers. |
| `_goal_notes_progress_v2.jsonl` | Append-only task log; **SUCCESS lines are the dedupe source**. |
| `_goal_notes_skip.txt` | BVs to never attempt (deleted videos, silent audio). |
| `_kb_copy_state.json` | `video_id -> KB path`; makes the copy and link steps idempotent. |
| `_kb_copy_report.md`, `_kb_source_link_report.md` | Per-run reports; check these after an import. |
| `_dedupe_reports/` | Why a video/part was dropped before generation. |

Media cache: `backend/data/data/<video_id>.{mp4,mp3,meta.json}`.
Notes: `backend/note_results/{task_id}_markdown.md` (+ `.json`, `_transcript.json`).

---

## Gotchas worth knowing before you start

- **Bilibili concurrency**: 2 download workers. More causes 412s and CDN timeouts.
- **Backend workers**: 8 for parsing. 32 exhausted the Windows commit limit
  (`WinError 1455`), producing `视频处理失败`.
- **Two backends**: 8483 is the normal one; `run_full_plan.py` starts 8484 with a
  larger worker pool. The driver picks one via `--api-base`.
- **Ark**: preflight with `--check`. `ModelNotOpen` means the model is not
  activated for the account; `SetLimitExceeded` means the usage cap was hit.
- **Deleting status files**: never bulk-delete `note_results/*.status.json` —
  match the exact task id. A glob once removed 5,238 `_markdown.status.json`
  markers; harmless, but avoidable.
