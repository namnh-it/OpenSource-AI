param([int]$Port = 8000)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    Write-Error 'Chua co moi truong. Chay .\scripts\setup.ps1 truoc.'
}

& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port $Port --reload
