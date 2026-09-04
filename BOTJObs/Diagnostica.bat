@echo off
REM =====================================================
REM DIAGNOSTICA - shows what the bot is doing
REM Double-click me to run the diagnostic report
REM =====================================================
cd /d "%~dp0"
echo.
echo =====================================================
echo   JOBMONITOR - DIAGNOSTIC REPORT
echo =====================================================
echo.
echo Please wait ~20 seconds (fetching live data from 3 companies)...
echo.
"C:\Users\dielomb\AppData\Local\Python\pythoncore-3.14-64\python.exe" diagnostic.py
echo.
echo =====================================================
pause
