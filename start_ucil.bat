@echo off
chcp 65001 > nul
title AuraX-UCIL Community Starter
cls
echo ===================================================================
echo   AuraX-UCIL Community Edition (v3.5 Free Open-Source)
echo   [원클릭 시작] 로컬 API 서버와 웹 UI를 기동합니다.
echo ===================================================================
cd /d "%~dp0"
python -c "import fastapi, uvicorn, pydantic" >nul 2>nul
if %errorlevel% neq 0 (
    echo [알림] 필수 라이브러리를 설치합니다...
    pip install fastapi uvicorn pydantic requests >nul 2>nul
)
start "UCIL_Community_Backend" /min python web_app\backend\main.py
timeout /t 2 /nobreak > nul
start "" "web_app\frontend\community_app.html"
echo [성공] 브라우저 화면이 열렸습니다.
echo 종료하려면 'stop_ucil.bat'을 실행하세요.
timeout /t 5 > nul
exit
