@echo off
title AuraX-UCIL Community Stopper
cls
echo ===================================================
echo   Stopping AuraX-UCIL Community Edition...
echo ===================================================
cd /d "%~dp0"

taskkill /F /FI "WINDOWTITLE eq UCIL_Community_Backend*" /T >nul 2>nul
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>nul
)

echo [DONE] All background services stopped successfully.
timeout /t 3 > nul
exit
