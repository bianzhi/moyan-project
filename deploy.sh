#!/bin/bash

# 墨岩缠论分析系统 - 离线Docker构建脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_message() {
    echo -e "${2}${1}${NC}"
}

print_message "🚀 墨岩缠论分析系统 - 离线Docker构建" $BLUE
print_message "======================================" $BLUE

# 检查是否存在Python环境
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    print_message "❌ 未找到Python环境" $RED
    exit 1
fi

print_message "✅ 找到Python: $($PYTHON_CMD --version)" $GREEN

# 检查Docker是否可用
if ! command -v docker &> /dev/null; then
    print_message "⚠️  Docker未安装，使用本地Python环境启动" $YELLOW
    
    # 创建必要目录
    mkdir -p output/charts output/reports logs
    
    # 安装依赖
    print_message "📦 安装Python依赖..." $YELLOW
    $PYTHON_CMD -m pip install -r requirements.txt
    
    # 启动服务
    print_message "🚀 启动服务..." $GREEN
    export PYTHONPATH=$(pwd)
    $PYTHON_CMD -m streamlit run src/moyan/web/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false &
    
    sleep 5
    print_message "✅ 服务已启动！" $GREEN
    print_message "📊 访问地址: http://localhost:8501" $BLUE
    
    exit 0
fi

# 尝试Docker构建
print_message "🐳 尝试Docker构建..." $YELLOW

# 检查网络连接
if ! docker pull hello-world &> /dev/null; then
    print_message "⚠️  Docker网络连接失败，回退到本地Python环境" $YELLOW
    
    mkdir -p output/charts output/reports logs
    
    print_message "📦 安装Python依赖..." $YELLOW
    $PYTHON_CMD -m pip install -r requirements.txt
    
    print_message "🚀 启动本地服务..." $GREEN
    export PYTHONPATH=$(pwd)
    $PYTHON_CMD -m streamlit run src/moyan/web/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false &
    
    sleep 5
    print_message "✅ 本地服务已启动！" $GREEN
    print_message "📊 访问地址: http://localhost:8501" $BLUE
    
    exit 0
fi

# Docker构建成功，继续Docker部署
print_message "🔨 Docker网络正常，开始构建镜像..." $GREEN

# 创建目录
mkdir -p output/charts output/reports logs

# 构建并启动
if command -v docker-compose &> /dev/null; then
    docker-compose build && docker-compose up -d
else
    docker compose build && docker compose up -d
fi

sleep 10

print_message "✅ Docker服务已启动！" $GREEN
print_message "📊 访问地址: http://localhost:8501" $BLUE
print_message "📁 分析结果: ./output/" $BLUE
print_message "📝 日志文件: ./logs/" $BLUE
