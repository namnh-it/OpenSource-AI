$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

& .\.venv\Scripts\ruff.exe check --fix app tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& .\.venv\Scripts\ruff.exe format app tests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
