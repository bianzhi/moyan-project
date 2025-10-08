@echo off
chcp 65001 >nul
echo 🚀 墨岩缠论分析系统 - Windows启动脚本
echo ==========================================
echo.

REM 检查是否在正确的目录
if not exist "docker-compose.yml" (
    echo ❌ 错误：未找到 docker-compose.yml 文件
    echo 💡 请确保在包含以下文件的目录中运行此脚本：
    echo    - moyan-czsc-docker.tar
    echo    - docker-compose.yml
    echo    - start-windows.bat
    echo.
    pause
    exit /b 1
)

REM 检查Docker是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未安装或未添加到PATH
    echo 💡 请先安装Docker Desktop：
    echo    https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

REM 检查Docker是否运行
echo 🔍 检查Docker服务状态...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未运行，请启动Docker Desktop
    echo 💡 启动步骤：
    echo    1. 双击桌面上的Docker Desktop图标
    echo    2. 等待Docker引擎启动完成（状态栏显示绿色）
    echo    3. 重新运行此脚本
    echo.
    pause
    exit /b 1
)

echo ✅ Docker服务运行正常

REM 检查镜像是否存在
echo 🔍 检查Docker镜像...
docker images moyan-project-moyan-czsc:latest -q >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Docker镜像不存在，开始导入...
    
    if not exist "moyan-czsc-docker.tar" (
        echo ❌ 错误：未找到 moyan-czsc-docker.tar 文件
        echo 💡 请确保镜像文件在当前目录中
        pause
        exit /b 1
    )
    
    echo 📥 正在导入Docker镜像（大约需要1-2分钟）...
    docker load -i moyan-czsc-docker.tar
    
    if %errorlevel% neq 0 (
        echo ❌ 镜像导入失败
        pause
        exit /b 1
    )
    
    echo ✅ 镜像导入成功
) else (
    echo ✅ Docker镜像已存在
)

REM 创建必要的目录
echo 📁 创建必要的目录...
if not exist "output" mkdir output
if not exist "output\charts" mkdir output\charts
if not exist "output\reports" mkdir output\reports
if not exist "logs" mkdir logs

REM 停止现有容器（如果存在）
echo 🛑 停止现有容器...
docker-compose down >nul 2>&1

REM 启动服务
echo 🚀 启动墨岩缠论分析系统...
docker-compose up -d

if %errorlevel% equ 0 (
    echo.
    echo ✅ 服务启动成功！
    echo.
    echo 📊 访问信息：
    echo    Web界面: http://localhost:8501
    echo    分析结果: .\output\charts\
    echo    分析报告: .\output\reports\
    echo    系统日志: .\logs\
    echo.
    echo 🎯 使用说明：
    echo    1. 打开浏览器访问 http://localhost:8501
    echo    2. 在左侧输入股票代码（如：000001、600036）
    echo    3. 选择K线级别和时间范围
    echo    4. 点击分析按钮开始缠论分析
    echo.
    echo 🛠️  常用命令：
    echo    停止服务: docker-compose down
    echo    查看日志: docker-compose logs -f
    echo    查看状态: docker-compose ps
    echo    重启服务: docker-compose restart
    echo.
    echo 💡 提示：保持此窗口打开，或按任意键关闭
    echo    服务将在后台继续运行
    echo.
    
    REM 尝试自动打开浏览器
    timeout /t 3 /nobreak >nul
    start http://localhost:8501 >nul 2>&1
    
    pause
) else (
    echo.
    echo ❌ 服务启动失败
    echo 🔍 请检查以下可能的原因：
    echo    1. 端口8501被其他程序占用
    echo    2. Docker Desktop内存不足（建议4GB+）
    echo    3. 防火墙阻止了Docker服务
    echo.
    echo 📋 故障排除步骤：
    echo    1. 运行: netstat -ano ^| findstr :8501
    echo    2. 检查Docker Desktop资源设置
    echo    3. 查看详细日志: docker-compose logs
    echo.
    pause
)
