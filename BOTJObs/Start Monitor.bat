@echo off
REM Starts the JobMonitor background task
powershell -Command "Start-ScheduledTask -TaskName 'JobMonitor_BOTJObs'; Start-Sleep 2; $t = Get-ScheduledTask -TaskName 'JobMonitor_BOTJObs'; Write-Host ('State: ' + $t.State) -ForegroundColor Green"
timeout /t 3 /nobreak >nul
