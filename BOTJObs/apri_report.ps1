# ============================================================
# APRI REPORT - Opens today's daily digest report in the browser.
# If today's report doesn't exist yet, generates it first.
# ============================================================
$ErrorActionPreference = "Continue"
$ProjectDir = "C:\Users\dielomb\Documents\BOTJObs"
$Python     = "C:\Users\dielomb\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$Today      = Get-Date -Format "yyyy-MM-dd"
$ReportPath = Join-Path $ProjectDir "data\reports\daily_$Today.html"

Set-Location $ProjectDir

if (-not (Test-Path $ReportPath)) {
    Write-Host "Today's report doesn't exist yet - generating..." -ForegroundColor Yellow
    & $Python main.py digest
    Start-Sleep -Seconds 1
}

if (Test-Path $ReportPath) {
    Write-Host "Opening report: $ReportPath" -ForegroundColor Cyan
    Start-Process $ReportPath
} else {
    Write-Host "ERROR: Report not found. Run a scan first with:" -ForegroundColor Red
    Write-Host "  python main.py once" -ForegroundColor Yellow
}
