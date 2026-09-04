# =====================================================
# SETUP AUTOSTART - Registers JobMonitor as a Windows
# Scheduled Task that starts at user logon and runs
# invisibly in the background 24/7.
# =====================================================
$ErrorActionPreference = "Stop"

$TaskName    = "JobMonitor_BOTJObs"
$ProjectDir  = "C:\Users\dielomb\Documents\BOTJObs"
$PythonW     = "C:\Users\dielomb\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  JobMonitor - AUTOSTART SETUP" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check pythonw.exe
if (-not (Test-Path $PythonW)) {
    Write-Host "ERROR: pythonw.exe not found at $PythonW" -ForegroundColor Red
    exit 1
}

# Remove existing task if present
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "Task already exists - unregistering old version..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Action: run pythonw.exe main.py loop  (windowless = no visible console)
$Action = New-ScheduledTaskAction `
    -Execute $PythonW `
    -Argument "main.py loop" `
    -WorkingDirectory $ProjectDir

# Trigger: at logon of THIS user (not all users)
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# Settings: robust for laptops (battery, wifi, restart on crash)
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit (New-TimeSpan -Days 365) `
    -MultipleInstances IgnoreNew

# Register (runs as current user, no admin needed, no password)
$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Silent job-page monitor. Scans 25 companies every 30 min, digest at 19:00." `
    -Force | Out-Null

Write-Host "OK - Task '$TaskName' registered." -ForegroundColor Green
Write-Host ""

# Start it now so it's already running
Write-Host "Starting task now (first scan will begin in the background)..." -ForegroundColor Cyan
Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 2

# Show status
$task = Get-ScheduledTask -TaskName $TaskName
$info = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Host ""
Write-Host "STATUS:" -ForegroundColor Cyan
Write-Host "  State:      $($task.State)" -ForegroundColor White
Write-Host "  Last run:   $($info.LastRunTime)" -ForegroundColor White
Write-Host "  Next run:   at every logon" -ForegroundColor White
Write-Host ""
Write-Host "MANAGE with these files (in $ProjectDir):" -ForegroundColor Cyan
Write-Host "  Start Monitor.bat   - starts the monitor" -ForegroundColor Gray
Write-Host "  Stop Monitor.bat    - stops it" -ForegroundColor Gray
Write-Host "  Status Monitor.bat  - shows if it's running" -ForegroundColor Gray
Write-Host "  Apri Report.bat     - opens today's report" -ForegroundColor Gray
Write-Host ""
Write-Host "DONE." -ForegroundColor Green
