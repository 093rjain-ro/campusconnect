@echo off
title CampusConnect SQLite Live Server
echo ============================================================
echo   Starting CampusConnect SQLite Backend Server
echo   Database: .db\campusconnect.db
echo   View live in DB Browser for SQLite: .db\campusconnect.db
echo ============================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Starting Python Flask SQLite server on http://localhost:5000...
    start http://localhost:5000
    python server.py
) else (
    echo [INFO] Python not found. Starting Node.js SQLite server on http://localhost:5000...
    start http://localhost:5000
    node server.js
)
pause
