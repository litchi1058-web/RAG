@echo off
chcp 65001 >nul
title 🐛 后端服务 [端口8000]
set PROJECT_DIR=%~dp0..
echo ============================================
echo         启动病虫害智能诊断系统 - 后端服务
echo ============================================
echo.

set PORT=8000

echo [1/2] 检查并释放端口 %PORT%...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
    echo 发现端口 %PORT% 被进程 %%a 占用，正在终止...
    taskkill /PID %%a /F >nul 2>&1
    if %errorlevel% equ 0 (
        echo 进程 %%a 已终止
    ) else (
        echo 终止进程 %%a 失败，请手动处理
    )
)

echo.
echo [2/2] 启动后端服务...
echo ============================================
echo 后端服务启动中，请等待...
echo 端口: %PORT%
echo ============================================
echo.

cd /d "%PROJECT_DIR%"
python -m uvicorn backend.main:app --host 0.0.0.0 --port %PORT%

pause