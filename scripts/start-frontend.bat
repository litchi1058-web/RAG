@echo off
chcp 65001 >nul
title 🌾 前端服务 [端口5174]
echo ============================================
echo         启动病虫害智能诊断系统 - 前端服务
echo ============================================
echo.

set PORT=5174

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
echo [2/2] 启动前端服务...
echo ============================================
echo 前端服务启动中，请等待...
echo 端口: %PORT%
echo ============================================
echo.

cd /d "%~dp0frontend"
npm run dev -- --port %PORT%

pause
