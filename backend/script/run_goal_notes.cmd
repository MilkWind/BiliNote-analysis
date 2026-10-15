@echo off
REM Long-running batch driver launched by the Task Scheduler (task: BiliNoteGoalNotes).
REM No time budget: a healthy run continues until every video is done. The repeating
REM trigger + IgnoreNew exists only for self-healing -- if the process is killed,
REM the next tick starts a fresh run that resumes from the DB/progress files.
cd /d D:\development-projects\study-projects\BiliNote-analysis\backend
.venv\Scripts\python.exe script\batch_goal_notes.py --concurrency 2 >> ..\goal_videos\_goal_notes_console.log 2>&1
