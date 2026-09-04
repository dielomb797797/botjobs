@echo off
REM Double-click me to open today's job report!
powershell -ExecutionPolicy Bypass -File "%~dp0apri_report.ps1"
timeout /t 2 /nobreak >nul
