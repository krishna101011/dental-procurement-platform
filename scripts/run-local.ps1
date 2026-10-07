$ErrorActionPreference = 'Stop'

# DENTRA / Dental Procurement Platform - reliable local launcher
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$python = Join-Path $backend '.venv\Scripts\python.exe'
$envFile = Join-Path $backend '.env'

if (!(Test-Path (Join-Path $backend 'app\main.py'))) {
  throw "Backend not found. Open PowerShell in the repository root: $root"
}
if (!(Test-Path (Join-Path $frontend 'package.json'))) {
  throw "Frontend not found. Open PowerShell in the repository root: $root"
}

Write-Host "`n[1/7] Configuring local SQLite database..." -ForegroundColor Cyan

if (!(Test-Path $envFile)) {
  Copy-Item (Join-Path $root '.env.example') $envFile
}

$raw = Get-Content $envFile -Raw
if ($raw -match '(?m)^DATABASE_URL=.*$') {
  $raw = $raw -replace '(?m)^DATABASE_URL=.*$', 'DATABASE_URL=sqlite:///./dental.db'
} else {
  $raw += "`nDATABASE_URL=sqlite:///./dental.db"
}
if ($raw -match '(?m)^CORS_ORIGINS=.*$') {
  $raw = $raw -replace '(?m)^CORS_ORIGINS=.*$', 'CORS_ORIGINS=http://127.0.0.1:5174,http://localhost:5174,http://127.0.0.1:5173,http://localhost:5173'
} else {
  $raw += "`nCORS_ORIGINS=http://127.0.0.1:5174,http://localhost:5174,http://127.0.0.1:5173,http://localhost:5173"
}
Set-Content $envFile $raw

Write-Host "[2/7] Preparing Python..." -ForegroundColor Cyan

if (!(Test-Path $python)) {
  if (!(Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' was not found. Install Python 3.11+ and enable the Python launcher."
  }
  py -3 -m venv (Join-Path $backend '.venv')
}

Write-Host "[3/7] Installing backend dependencies..." -ForegroundColor Cyan
& $python -m pip install -r (Join-Path $backend 'requirements.txt')

Write-Host "[4/7] Initializing local database..." -ForegroundColor Cyan
Push-Location $backend
try {
  & $python -m app.db.seed
} finally {
  Pop-Location
}

Write-Host "[5/7] Installing frontend dependencies..." -ForegroundColor Cyan
if (Get-Command pnpm -ErrorAction SilentlyContinue) {
  & pnpm --dir $frontend install
} elseif (Get-Command npm -ErrorAction SilentlyContinue) {
  & npm --prefix $frontend install
} else {
  throw "Neither pnpm nor npm is installed."
}

Write-Host "[6/7] Clearing old project ports..." -ForegroundColor Cyan
foreach ($port in 8000,5173,5174) {
  Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
}

Write-Host "[7/7] Starting backend and frontend..." -ForegroundColor Cyan

Start-Process powershell.exe -WorkingDirectory $backend -ArgumentList @(
  '-NoExit',
  '-Command',
  "& '$python' -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
)

$frontendCmd = if (Get-Command pnpm -ErrorAction SilentlyContinue) {
  "pnpm dev -- --host 127.0.0.1 --port 5174"
} else {
  "npm run dev -- --host 127.0.0.1 --port 5174"
}
Start-Process powershell.exe -WorkingDirectory $frontend -ArgumentList @(
  '-NoExit',
  '-Command',
  $frontendCmd
)

Write-Host "Waiting for backend..." -ForegroundColor Yellow
$backendReady = $false
for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 1
  try {
    $r = Invoke-WebRequest 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 2
    if ($r.StatusCode -eq 200) { $backendReady = $true; break }
  } catch {}
}
if (!$backendReady) {
  throw "Backend did not become ready. Check the backend PowerShell window for the first error message."
}

Write-Host "Waiting for frontend..." -ForegroundColor Yellow
$frontendReady = $false
for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 1
  try {
    $r = Invoke-WebRequest 'http://127.0.0.1:5174/' -UseBasicParsing -TimeoutSec 2
    if ($r.StatusCode -eq 200) { $frontendReady = $true; break }
  } catch {}
}
if (!$frontendReady) {
  throw "Frontend did not become ready. Check the frontend PowerShell window."
}

Write-Host "`n==============================================" -ForegroundColor Green
Write-Host " DENTAL PROCUREMENT PLATFORM READY" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host "Frontend : http://127.0.0.1:5174/" -ForegroundColor White
Write-Host "Backend  : http://127.0.0.1:8000/" -ForegroundColor White
Write-Host "Swagger  : http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "Health   : http://127.0.0.1:8000/health" -ForegroundColor White
Write-Host "==============================================`n" -ForegroundColor Green

Start-Process 'http://127.0.0.1:5174/'
