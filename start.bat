@echo off
REM 墨岩缠论分析系统 Docker 启动脚本 (Windows)
REM Moyan CZSC Analysis System Docker Startup Script (Windows)

echo 🚀 墨岩缠论分析系统 Docker 启动脚本
echo ==================================

REM 检查Docker是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未安装，请先安装 Docker Desktop
    pause
    exit /b 1
)

REM 检查Docker Compose是否可用
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    docker compose version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Docker Compose 未安装，请先安装 Docker Compose
        pause
        exit /b 1
    )
    set COMPOSE_CMD=docker compose
) else (
    set COMPOSE_CMD=docker-compose
)

REM 创建必要的目录
echo 📁 创建必要的目录...
if not exist "output\charts" mkdir output\charts
if not exist "output\reports" mkdir output\reports
if not exist "logs" mkdir logs

REM 构建Docker镜像
echo 🔨 构建 Docker 镜像...
%COMPOSE_CMD% build
if %errorlevel% neq 0 (
    echo ❌ Docker 镜像构建失败
    pause
    exit /b 1
)

REM 启动服务
echo 🚀 启动墨岩缠论分析系统...
%COMPOSE_CMD% up -d
if %errorlevel% neq 0 (
    echo ❌ 服务启动失败
    pause
    exit /b 1
)

REM 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 10 /nobreak >nul

echo.
echo ✅ 墨岩缠论分析系统已成功启动！
echo 📊 访问地址: http://localhost:8501
echo 📁 分析结果保存在: .\output\
echo 📝 日志文件保存在: .\logs\
echo.
echo 常用命令:
echo   查看日志: %COMPOSE_CMD% logs -f
echo   停止服务: %COMPOSE_CMD% down
echo   重启服务: %COMPOSE_CMD% restart
echo.
pause
