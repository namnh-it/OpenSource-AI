$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if (-not (Test-Path '.venv')) {
    python -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

if (-not (Test-Path '.env')) {
    Copy-Item .env.example .env
    Write-Host 'Da tao .env. Hay them AITC_API_KEY truoc khi goi AI that.' -ForegroundColor Yellow
}

& .\.venv\Scripts\python.exe -m app.cli doctor
