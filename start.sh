#!/bin/bash

# 墨岩缠论分析系统 Docker 启动脚本
# Moyan CZSC Analysis System Docker Startup Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${2}${1}${NC}"
}

print_message "🚀 墨岩缠论分析系统 Docker 启动脚本" $BLUE
print_message "==================================" $BLUE

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    print_message "❌ Docker 未安装，请先安装 Docker" $RED
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_message "❌ Docker Compose 未安装，请先安装 Docker Compose" $RED
    exit 1
fi

# 创建必要的目录
print_message "📁 创建必要的目录..." $YELLOW
mkdir -p output/charts output/reports logs

# 构建Docker镜像
print_message "🔨 构建 Docker 镜像..." $YELLOW
if command -v docker-compose &> /dev/null; then
    docker-compose build
else
    docker compose build
fi

# 启动服务
print_message "🚀 启动墨岩缠论分析系统..." $GREEN
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    docker compose up -d
fi

# 等待服务启动
print_message "⏳ 等待服务启动..." $YELLOW
sleep 10

# 检查服务状态
if command -v docker-compose &> /dev/null; then
    if docker-compose ps | grep -q "Up"; then
        print_message "✅ 服务启动成功！" $GREEN
    else
        print_message "❌ 服务启动失败，请检查日志" $RED
        docker-compose logs
        exit 1
    fi
else
    if docker compose ps | grep -q "running"; then
        print_message "✅ 服务启动成功！" $GREEN
    else
        print_message "❌ 服务启动失败，请检查日志" $RED
        docker compose logs
        exit 1
    fi
fi

print_message "" $NC
print_message "🎉 墨岩缠论分析系统已成功启动！" $GREEN
print_message "📊 访问地址: http://localhost:8501" $BLUE
print_message "📁 分析结果保存在: ./output/" $BLUE
print_message "📝 日志文件保存在: ./logs/" $BLUE
print_message "" $NC
print_message "常用命令:" $YELLOW
print_message "  查看日志: docker-compose logs -f" $NC
print_message "  停止服务: docker-compose down" $NC
print_message "  重启服务: docker-compose restart" $NC
print_message "" $NC
