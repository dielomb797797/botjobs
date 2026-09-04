# ============================================================
# JOB MONITOR - Launch script
# Modes: once / loop / digest / test
# ============================================================
$ErrorActionPreference = "Stop"
$ProjectDir = "C:\Users\dielomb\Documents\BOTJObs"
$Python     = "C:\Users\dielomb\AppData\Local\Python\pythoncore-3.14-64\python.exe"

Set-Location $ProjectDir

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  JOB MONITOR - BOTJObs" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

$Mode = $args[0]
if (-not $Mode) { $Mode = "loop" }

Write-Host "Mode: $Mode" -ForegroundColor Yellow
Write-Host ""

& $Python main.py $Mode
