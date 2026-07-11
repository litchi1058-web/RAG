@echo off
chcp 65001 >nul 2>&1
title Disease Recognition System

set ROOT=%~dp0
cd /d "%ROOT%"

echo ========================================
echo  Disease Recognition and RAG Diagnosis System
echo  One-click Startup Script (v2.1)
echo ========================================
echo.

echo --- Environment Check ---
where python >nul 2>&1
if %errorlevel% neq 0 ( echo [FAIL] Python not found & pause & exit /b 1 )
for /f "delims=" %%i in ('python --version 2^>^&1') do set PY_VER=%%i
echo [OK] %PY_VER%
where node >nul 2>&1
if %errorlevel% neq 0 ( echo [FAIL] Node.js not found & pause & exit /b 1 )
for /f "delims=" %%i in ('node --version') do set NODE_VER=%%i
echo [OK] Node.js %NODE_VER%
echo.

echo --- Cleaning old services ---
for %%p in (8000 8001 5173) do (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%p " ^| findstr LISTENING') do (
        taskkill /f /pid %%a >nul 2>&1
    )
)
echo [OK] Old services cleaned
echo.

echo [1/3] AI Service :8001
set PYTHONPATH=%ROOT%
start "AI:8001" cmd /k "title AI:8001 && cd /d ""%ROOT%"" && python ai_service\main.py"
ping -n 6 -w 1000 127.0.0.1 >nul

echo [2/3] Backend API :8000
start "API:8000" cmd /k "title API:8000 && cd /d ""%ROOT%"" && set PYTHONPATH=%ROOT% && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
ping -n 6 -w 1000 127.0.0.1 >nul

echo [3/3] Frontend UI :5173
start "UI:5173" cmd /k "title UI:5173 && cd /d ""%ROOT%frontend"" && npm run dev"

echo.
echo Waiting for services to start...
ping -n 11 -w 1000 127.0.0.1 >nul
echo.

echo --- Service Status ---
python -c "import urllib.request; r=urllib.request.urlopen('http://localhost:8000/api/health',timeout=3); print('[Backend] :8000 OK' if r.status==200 else '[Backend] FAIL')" 2>nul || echo [Backend] :8000 Not responding
python -c "import urllib.request,json; r=json.loads(urllib.request.urlopen('http://localhost:8001/ai/health',timeout=3).read()); print('[AI]      :8001 OK GPU='+r.get('device',''))" 2>nul || echo [AI]      :8001 Loading...
python -c "import urllib.request; r=urllib.request.urlopen('http://localhost:5173',timeout=3); print('[Frontend] :5173 OK')" 2>nul || echo [Frontend] :5173 Checking...
echo.

echo ========================================
echo           STARTUP COMPLETE
echo ========================================
echo.
echo  [Frontend] http://localhost:5173
echo  [Backend]  http://localhost:8000/docs
echo  [AI]       http://localhost:8001/ai/health
echo.
echo  [Login] admin / admin123
echo.
pause
