@echo off
REM Long-running v2 batch driver (Ark, 2026-10 source set).
REM Resumes automatically from bili_note.db + _goal_notes_progress_v2.jsonl.
REM If the process is killed, run this again (or schedule it) to continue.
cd /d D:\development-projects\study-projects\BiliNote-analysis\backend
.venv\Scripts\python.exe script\batch_goal_notes_v2.py --concurrency 3 --poll 20 --stall 7200 >> ..\goal_videos\_goal_notes_v2_console.log 2>&1
