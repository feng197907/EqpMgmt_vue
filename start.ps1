# Equipment Management System - Startup Script
$ErrorActionPreference = "Continue"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Equipment Management System - Startup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Please install Python 3.9+" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "[OK] Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Node.js not found. Please install Node.js 16+" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check / Install frontend dependencies
if (-not (Test-Path "$ProjectDir\frontend\node_modules")) {
    Write-Host "[Frontend] node_modules not found, installing dependencies..." -ForegroundColor Yellow
    Push-Location "$ProjectDir\frontend"
    npm install
    $exitCode = $LASTEXITCODE
    Pop-Location
    if ($exitCode -ne 0) {
        Write-Host "[ERROR] npm install failed" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Start Backend
Write-Host "[Backend] Starting FastAPI on port 8000..." -ForegroundColor Green
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd /d `"$ProjectDir`" & uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"

# Wait a moment for backend to init
Start-Sleep -Seconds 2

# Start Frontend
Write-Host "[Frontend] Starting Vite dev server on port 5173..." -ForegroundColor Green
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd /d `"$ProjectDir\frontend`" & npm run dev"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Enter to close this window (services will keep running)"
Read-Host
