# One-command demo: starts API + UI and opens the browser
$ErrorActionPreference = "Stop"
$RagRoot = Split-Path $PSScriptRoot -Parent
$ProjectsRoot = Split-Path $RagRoot -Parent
$Backend = Join-Path $RagRoot "backend"
$Frontend = Join-Path $ProjectsRoot "RAG-Chatbot-Frontend\frontend"
$VenvPython = Join-Path $Backend "venv\Scripts\python.exe"

Write-Host "Aura Enterprise Demo Launcher" -ForegroundColor Cyan
Write-Host "  Backend:  $Backend"
Write-Host "  Frontend: $Frontend"

if (-not (Test-Path (Join-Path $Backend ".env"))) {
    Copy-Item (Join-Path $Backend ".env.example") (Join-Path $Backend ".env")
    Write-Host "`nCreated backend/.env — add GOOGLE_API_KEY before chatting." -ForegroundColor Yellow
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Gray
    python -m venv (Join-Path $Backend "venv")
    & (Join-Path $Backend "venv\Scripts\pip.exe") install -r (Join-Path $Backend "requirements.txt")
}

if (-not (Test-Path $Frontend)) {
    Write-Host "Frontend not found at $Frontend" -ForegroundColor Red
    exit 1
}

Write-Host "`nStarting API on http://127.0.0.1:8000 ..." -ForegroundColor Green
$apiJob = Start-Process -FilePath $VenvPython -ArgumentList "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000" -WorkingDirectory $Backend -PassThru -WindowStyle Minimized

Write-Host "Starting UI on http://127.0.0.1:5500 ..." -ForegroundColor Green
$uiJob = Start-Process -FilePath "python" -ArgumentList "-m", "http.server", "5500", "--bind", "127.0.0.1" -WorkingDirectory $Frontend -PassThru -WindowStyle Minimized

Start-Sleep -Seconds 3
$url = "http://127.0.0.1:5500/?api=http://127.0.0.1:8000"
Write-Host "`nOpening $url" -ForegroundColor Cyan
Start-Process $url

Write-Host @"

Demo is running (minimized windows).
  API:  http://127.0.0.1:8000/docs
  UI:   $url

To stop:
  Stop-Process -Id $($apiJob.Id),$($uiJob.Id) -Force

"@ -ForegroundColor Gray
