# Equipment Management System - Startup Script
$ErrorActionPreference = "Continue"

$ProjectDir = $PSScriptRoot

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Equipment Management System - Startup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ----- Check Python -----
try {
    $pyVer = python --version 2>&1
    Write-Host "[OK] Python: $pyVer" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Please install Python 3.9+" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# ----- Check Node.js -----
try {
    $nodeVer = node --version 2>&1
    Write-Host "[OK] Node.js: $nodeVer" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Node.js not found. Please install Node.js 16+" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# ----- Activate virtual env -----
$venvActivate = Join-Path $ProjectDir ".venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    Write-Host "[Info] Activating virtual environment..." -ForegroundColor Yellow
    . $venvActivate
}

# ----- Kill existing processes on target ports -----
Write-Host "[Info] Cleaning up existing processes on ports 8000/5173..." -ForegroundColor Yellow
@(8000, 5173) | ForEach-Object {
    $conns = netstat -ano | Select-String ":$_\s" | Select-String "LISTENING"
    foreach ($line in $conns) {
        $pidStr = ($line -split '\s+')[-1]
        if ($pidStr -match '^\d+$') {
            taskkill /F /PID $pidStr 2>$null | Out-Null
        }
    }
}

# ----- Install frontend dependencies if needed -----
if (-not (Test-Path "$ProjectDir\frontend\node_modules")) {
    Write-Host "[Frontend] Installing dependencies..." -ForegroundColor Yellow
    Push-Location "$ProjectDir\frontend"
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] npm install failed" -ForegroundColor Red
        Pop-Location
        Read-Host "Press Enter to exit"
        exit 1
    }
    Pop-Location
}

# ----- Start Backend -----
Write-Host ""
Write-Host "[Backend] Starting FastAPI on port 8000..." -ForegroundColor Green
$backendArgs = "/c cd /d `"$ProjectDir`" && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"
Start-Process -FilePath "cmd.exe" -ArgumentList $backendArgs

# ----- Wait for backend health check -----
Write-Host "[Backend] Waiting for backend to be ready..." -ForegroundColor Yellow
$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($r.StatusCode -eq 200) {
            Write-Host "[Backend] Ready! (http://127.0.0.1:8000)" -ForegroundColor Green
            $ready = $true
            break
        }
    } catch {}
}
if (-not $ready) {
    Write-Host "[WARN] Backend may not be ready, starting frontend anyway..." -ForegroundColor Yellow
}

# ----- Start Frontend -----
Write-Host ""
Write-Host "[Frontend] Starting Vite dev server on port 5173..." -ForegroundColor Green
$frontendArgs = "/c cd /d `"$ProjectDir\frontend`" && npm run dev"
Start-Process -FilePath "cmd.exe" -ArgumentList $frontendArgs

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Enter to close this window (services keep running)"
Read-Host
