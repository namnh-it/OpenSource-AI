$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

& .\.venv\Scripts\ruff.exe check app tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& .\.venv\Scripts\python.exe -m pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& .\.venv\Scripts\python.exe -c "from fastapi.testclient import TestClient; from app.main import app; assert TestClient(app).get('/api/ai/health').status_code == 200; print('health check passed')"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
