# Desktop Packaging — Problem Record

*Started: 2026-08-10*

This log tracks every problem encountered while packaging BiliNote as a desktop client (Tauri + PyInstaller), who solved it, and the current blocker.

---

## Environment snapshot

| Tool | Status at start |
|---|---|
| Node.js | v22.20.0 ✅ |
| pnpm | 11.20.0 ✅ |
| Rust / Cargo | 1.97.1 installed, **not on PATH** ⚠️ |
| Tauri CLI | 2.10.1 (local, via `node_modules/.bin`) ✅ |
| PyInstaller | 6.20.0 (global), 6.13.0 (venv) ✅ |
| FFmpeg | **not installed anywhere** ❌ |
| Backend deps | **not installed** (no venv, no fastapi/uvicorn/yt_dlp) ❌ |
| Python | default 3.14; also 3.12, 3.13 installed |

---

## Problems (in order)

### 1. Rust / Cargo not on PATH
- **Description**: `rustc`/`cargo` live at `%USERPROFILE%\.cargo\bin` but `build.bat` and `pnpm tauri build` both call them and PATH doesn't include that dir.
- **Solved by**: Me — prepend `%USERPROFILE%\.cargo\bin` to PATH when invoking the build.
- **Status**: Resolved (workaround only; permanent PATH fix still pending on user's side).

### 2. FFmpeg missing (required at runtime)
- **Description**: `ensure_ffmpeg_or_raise` is called at startup; FFmpeg was nowhere on disk/PATH.
- **First attempt**: `winget install Gyan.FFmpeg` → failed with `InternetOpenUrl() failed. 0x80072efd` (GitHub download blocked/unreachable).
- **Solved by**: **User** — manually downloaded FFmpeg to `D:\media-tools\ffmpeg-2026-08-06-git-essentials_build\bin`.
- **Status**: Resolved (verified `ffmpeg -version` works).

### 3. Backend Python dependencies not installed
- **Description**: No venv existed; `fastapi`, `uvicorn`, `yt_dlp`, `sqlalchemy` etc. failed to import in all 3 installed Pythons.
- **Decision**: User chose **Python 3.13** (best wheel coverage for compiled deps like ctranslate2/av/weasyprint vs. the riskier default 3.14).
- **Solved by**: Me — created `backend\.venv` with Python 3.13.3, then installed `requirements.txt`. User later re-ran the install to completion.
- **Status**: Resolved.

### 4. `pkg_resources` missing (faster-whisper / ctranslate2)
- **Description**: `import ctranslate2` failed with `ModuleNotFoundError: No module named 'pkg_resources'`. Fresh venv installed setuptools 84.x which **removed** `pkg_resources`.
- **Solved by**: Me — pinned `setuptools<81` (80.10.2). Verified `import faster_whisper, ctranslate2, av, ffmpeg` all pass.
- **Status**: Resolved.

### 5. Backend PyInstaller build
- **Description**: Running `backend\build.bat` — needed correct PATH (venv + Rust + FFmpeg).
- **Solved by**: Me — ran it with the full PATH; produced `BiliNoteBackend-x86_64-pc-windows-msvc.exe` (27.6 MB) with `.env` and `_internal/` bundled correctly.
- **Status**: Resolved.

### 6. Tauri build — MSI succeeded, NSIS failed (GitHub download timeout)  ⚠️ CURRENT BLOCKER
- **Description**: `pnpm tauri build` compiles the Rust app (✅ `app.exe` built) and produces the MSI bundle (✅ `BiliNote_2.4.4_x64_en-US.msi`, 136 MB). But the NSIS step downloads `nsis-3.11.zip` from `github.com/tauri-apps/binary-releases` and the download **repeatedly times out** (`failed to bundle project 'timeout: global'`). Retried 3 times — same failure. The WiX download earlier succeeded on retry, but NSIS never got through.
- **Attempts so far**:
  - Retried `pnpm tauri build` → still timed out.
  - Manually downloaded `nsis-3.11.zip` via `curl` with retries (2.25 MB, succeeded) into `%LOCALAPPDATA%\tauri\`.
  - Extracted to `%LOCALAPPDATA%\tauri\NSIS\nsis-3.11\`.
  - Re-ran build → bundler said `NSIS directory is missing some files. Recreating it.` and tried to re-download → timed out again. So my manual cache layout doesn't match what the bundler verifies.
  - Was fetching tauri-bundler source (tag `tauri-cli-v2.10.1`) to learn the exact expected cache path/layout, but the raw GitHub fetch returned 404 (wrong tag path) right before this log was requested.
- **Root cause (hypothesis)**: GitHub connectivity from this machine is flaky (WiX and manual curl worked intermittently). The bundler either needs a different cache layout or a reliable download.
- **Status**: **BLOCKED** — no successful NSIS installer yet, though the MSI installer already exists and is usable.
- **Remaining options**: figure out the exact NSIS cache layout the bundler expects (place `makensis.exe` etc. correctly); use `TAURI_BUNDLER_TOOLS_GITHUB_MIRROR` env var to point at a mirror/proxy; or ship the MSI as-is.

---

## Summary

- Solved by me (4): Rust PATH workaround, backend venv + requirements, setuptools pin, PyInstaller backend build.
- Solved by user (1): FFmpeg installation.
- **Currently blocking (1)**: NSIS tooling download timeout during `pnpm tauri build`.
