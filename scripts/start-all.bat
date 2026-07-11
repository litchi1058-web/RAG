@echo off
chcp 65001
echo ========================================
echo  Disease Recognition and RAG Diagnosis System
echo ========================================
echo.

echo [清理旧进程]
taskkill /F /IM node.exe 2>nul
taskkill /F /IM python.exe 2>nul

echo.
echo [1/3] 启动 AI 服务（加载 GGUF 模型）:8001
set PYTHONPATH=%~dp0
start cmd /k "title AI:8001 && cd /d %~dp0 && set PYTHONPATH=%~dp0 && python ai_service\main.py"

echo [2/3] 启动后端服务:8000
start cmd /k "title API:8000 && cd /d %~dp0 && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

echo [3/3] 启动前端服务:5174
start cmd /k "title UI:5174 && cd /d %~dp0frontend && npm run dev -- --port 5174"

echo.
echo 等待服务启动...
timeout /t 8

echo.
echo --- 服务状态 ---
python -c "import urllib.request; r=urllib.request.urlopen('http://localhost:8000/api/health',timeout=3); print('[Backend] :8000 OK')" 2>nul || echo [Backend] :8000 加载中...
python -c "import urllib.request,json; r=json.loads(urllib.request.urlopen('http://localhost:8001/ai/health',timeout=3).read()); print('[AI]      :8001 OK GPU='+r.get('device',''))" 2>nul || echo [AI]      :8001 加载中...
echo.

echo ========================================
echo           服务启动完成
echo ========================================
echo.
echo  [前端] http://localhost:5174
echo  [后端] http://localhost:8000/docs
echo  [AI]   http://localhost:8001/ai/health
echo.
echo  [登录] admin / admin123
echo.
start http://localhost:5174
