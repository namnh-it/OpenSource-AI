param(
    [Parameter(Mandatory = $true)][string]$File,
    [ValidateSet('review', 'debug')][string]$Mode = 'review',
    [string]$Context = '',
    [string]$Model = 'gpt-6-luna'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

if (-not (Test-Path '.venv\Scripts\python.exe')) {
    Write-Error 'Chua co moi truong. Chay .\scripts\setup.ps1 truoc.'
}

# Review output is advice. Apply a patch manually, then run .\scripts\verify.ps1.
& .\.venv\Scripts\python.exe -m app.cli review --file $File --mode $Mode --context $Context --model $Model
