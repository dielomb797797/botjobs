@echo off
REM Stops the JobMonitor background task
powershell -Command "Stop-ScheduledTask -TaskName 'JobMonitor_BOTJObs' -ErrorAction SilentlyContinue; Get-Process pythonw -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'main.py' } | Stop-Process -Force; Write-Host 'JobMonitor stopped.' -ForegroundColor Yellow"
timeout /t 3 /nobreak >nul
