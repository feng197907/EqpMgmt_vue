@echo off
chcp 65001 >nul 2>&1
title DMS Startup

echo ============================================
echo   Equipment Management System - Startup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

:: Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install Node.js 16+
    pause
    exit /b 1
)

set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

:: ===== Start Backend (FastAPI) =====
echo [Backend] Starting FastAPI on port 8000...
start "Backend-FastAPI" cmd /c "cd /d %PROJECT_DIR% & uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

:: ===== Start Frontend (Vite) =====
echo [Frontend] Starting Vite dev server on port 5173...
start "Frontend-Vite" cmd /c "cd /d %PROJECT_DIR%\frontend & npm run dev"

echo.
echo ============================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo ============================================
echo.
echo Press any key to close this window (services will keep running)
pause >nul
