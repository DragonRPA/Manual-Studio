@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"name = 'python.exe'\" | Where-Object { $_.CommandLine -like '*manual_capture_studio*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1
python manual_capture_studio.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application terminated unexpectedly. Error code: %ERRORLEVEL%
    pause
)
