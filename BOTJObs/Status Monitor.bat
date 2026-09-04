@echo off
REM Shows JobMonitor status
powershell -Command "$t = Get-ScheduledTask -TaskName 'JobMonitor_BOTJObs' -ErrorAction SilentlyContinue; if ($t) { $i = Get-ScheduledTaskInfo -TaskName 'JobMonitor_BOTJObs'; Write-Host ''; Write-Host 'JOBMONITOR STATUS' -ForegroundColor Cyan; Write-Host '=================' -ForegroundColor Cyan; Write-Host ('State:       ' + $t.State) -ForegroundColor White; Write-Host ('Last run:    ' + $i.LastRunTime) -ForegroundColor White; Write-Host ('Last result: ' + $i.LastTaskResult) -ForegroundColor White; Write-Host ('Next run:    ' + $i.NextRunTime) -ForegroundColor White; $p = Get-Process pythonw -ErrorAction SilentlyContinue; if ($p) { Write-Host ('Process:     RUNNING (PID ' + $p[0].Id + ')') -ForegroundColor Green } else { Write-Host 'Process:     NOT RUNNING' -ForegroundColor Yellow } } else { Write-Host 'Task not registered. Run setup_autostart.ps1 first.' -ForegroundColor Red }"
echo.
pause
