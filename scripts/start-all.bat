@echo off
chcp 65001 >nul
set PROJECT_DIR=%~dp0..
echo ============================================
echo  Disease Recognition and RAG Diagnosis System
echo ============================================
echo.

echo [Cleaning old processes]
taskkill /F /IM node.exe 2>nul
taskkill /F /IM python.exe 2>nul

echo.
echo [1/3] Starting AI Service (GGUF Model):8001
start cmd /k "title AI:8001 && cd /d %PROJECT_DIR% && set PYTHONPATH=%PROJECT_DIR% && python ai_service\main.py"

echo [2/3] Starting Backend Service:8000
start cmd /k "title API:8000 && cd /d %PROJECT_DIR% && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

echo [3/3] Starting Frontend Service:5174
start cmd /k "title UI:5174 && cd /d %PROJECT_DIR%\frontend && npm run dev -- --port 5174"

echo.
echo Waiting for services to start...
ping -n 9 127.0.0.1 >nul

echo.
echo --- Service Status ---
python -c "import urllib.request; r=urllib.request.urlopen('http://localhost:8000/api/health',timeout=3); print('[Backend] :8000 OK')" 2>nul || echo [Backend] :8000 Loading...
python -c "import urllib.request,json; r=json.loads(urllib.request.urlopen('http://localhost:8001/ai/health',timeout=3).read()); print('[AI]      :8001 OK GPU='+r.get('device',''))" 2>nul || echo [AI]      :8001 Loading...
echo.

echo ============================================
echo           Services Started Successfully
echo ============================================
echo.
echo  Frontend: http://localhost:5174
echo  Backend:  http://localhost:8000/docs
echo  AI:       http://localhost:8001/ai/health
echo.
echo  Login: admin / admin123
echo.
start http://localhost:5174