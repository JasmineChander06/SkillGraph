@echo off
title SkillGraph Local Server
cd /d "%~dp0backend"
echo ========================================================
echo  SkillGraph is starting at http://localhost:8000
echo  Press Ctrl+C to stop the server
echo ========================================================
echo.
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause

