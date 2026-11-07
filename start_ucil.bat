@echo off
title AuraX-UCIL Community Starter
cls
echo ===================================================
echo   AuraX-UCIL Community Edition (v3.5)
echo   Starting Local Backend API and Web UI...
echo ===================================================
cd /d "%~dp0"

start "UCIL_Community_Backend" /min python web_app\backend\main.py
timeout /t 2 /nobreak > nul
start "" "web_app\frontend\community_app.html"

echo [SUCCESS] Web Workspace opened in browser!
echo To exit cleanly, double-click 'stop_ucil.bat'.
timeout /t 4 > nul
exit
