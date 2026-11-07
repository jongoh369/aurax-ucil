@echo off
chcp 65001 > nul
title AuraX-UCIL Community Stopper
cls
echo ===================================================================
echo   AuraX-UCIL Community Edition 종료 중...
echo ===================================================================
taskkill /F /FI "WINDOWTITLE eq UCIL_Community_Backend*" /T >nul 2>nul
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>nul
)
echo [완료] 모든 프로세스가 안전하게 종료되었습니다.
timeout /t 3 > nul
exit
