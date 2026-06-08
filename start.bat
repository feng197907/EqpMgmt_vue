@echo off
chcp 65001 >nul 2>&1
title DMS Startup
setlocal enabledelayedexpansion

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
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

:: Activate virtual env if exists
if exist "%PROJECT_DIR%\.venv\Scripts\activate.bat" (
    echo [Info] Activating virtual environment...
    call "%PROJECT_DIR%\.venv\Scripts\activate.bat"
)

:: Kill existing processes on target ports
echo [Info] Cleaning up existing processes on ports 8000/5173...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING 2^>nul') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: Install frontend dependencies if needed
if not exist "%PROJECT_DIR%\frontend\node_modules" (
    echo [Frontend] Installing dependencies...
    cd /d "%PROJECT_DIR%\frontend"
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] npm install failed
        pause
        exit /b 1
    )
)

:: ===== Start Backend =====
echo.
echo [Backend] Starting FastAPI on port 8000...
start "Backend-FastAPI" cmd /c "cd /d %PROJECT_DIR% && .venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait for backend to be ready
echo [Backend] Waiting for backend to be ready...
set "RETRY=0"
:wait_backend
timeout /t 1 >nul
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/')" >nul 2>&1
if %errorlevel% neq 0 (
    set /a RETRY+=1
    if !RETRY! lss 15 goto wait_backend
    echo [WARN] Backend may not be ready, starting frontend anyway...
) else (
    echo [Backend] Ready! (http://127.0.0.1:8000)
)

:: ===== Start Frontend =====
echo.
echo [Frontend] Starting Vite dev server on port 5173...
start "Frontend-Vite" cmd /c "cd /d %PROJECT_DIR%\frontend && npm run dev"

echo.
echo ============================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo ============================================
echo.
echo Press any key to close this window (services keep running)
pause >nul
