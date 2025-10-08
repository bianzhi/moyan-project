#!/bin/bash

# Docker镜像构建脚本 - 配置国内镜像源

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_message() {
    echo -e "${2}${1}${NC}"
}

print_message "🐳 Docker镜像构建脚本" $BLUE
print_message "===================" $BLUE

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    print_message "❌ Docker未运行，请启动Docker Desktop" $RED
    exit 1
fi

print_message "✅ Docker运行正常" $GREEN

# 尝试配置Docker镜像源
print_message "🔧 配置Docker镜像源..." $YELLOW

# 创建或更新daemon.json（仅在macOS/Linux上）
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    DOCKER_CONFIG="$HOME/.docker/daemon.json"
    mkdir -p "$HOME/.docker"
    
    cat > "$DOCKER_CONFIG" << 'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ],
  "insecure-registries": [],
  "debug": false,
  "experimental": false
}
EOF
    
    print_message "📝 已配置Docker镜像源: $DOCKER_CONFIG" $YELLOW
    print_message "⚠️  请重启Docker Desktop以使配置生效" $YELLOW
    print_message "⏳ 等待10秒后继续..." $YELLOW
    sleep 10
fi

# 尝试构建镜像
print_message "🔨 开始构建Docker镜像..." $GREEN

# 创建必要目录
mkdir -p output/charts output/reports logs

# 尝试构建
if docker-compose build --no-cache; then
    print_message "✅ Docker镜像构建成功！" $GREEN
    
    # 查看构建的镜像
    print_message "📋 查看构建的镜像:" $BLUE
    docker images | grep -E "(moyan|REPOSITORY)"
    
    # 导出镜像
    IMAGE_NAME=$(docker-compose config --services | head -1)
    PROJECT_NAME=$(basename $(pwd) | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')
    FULL_IMAGE_NAME="${PROJECT_NAME}_${IMAGE_NAME}:latest"
    
    print_message "💾 导出Docker镜像..." $YELLOW
    if docker save -o moyan-czsc-docker.tar "$FULL_IMAGE_NAME"; then
        print_message "✅ 镜像已导出: moyan-czsc-docker.tar" $GREEN
        print_message "📦 镜像文件大小: $(du -h moyan-czsc-docker.tar | cut -f1)" $BLUE
    else
        print_message "⚠️  镜像导出失败，但构建成功" $YELLOW
    fi
    
    # 启动服务
    print_message "🚀 启动Docker服务..." $GREEN
    docker-compose up -d
    
    sleep 10
    
    print_message "🎉 Docker部署完成！" $GREEN
    print_message "📊 访问地址: http://localhost:8501" $BLUE
    
else
    print_message "❌ Docker镜像构建失败" $RED
    print_message "🔄 回退到本地Python环境..." $YELLOW
    
    # 启动本地服务
    export PYTHONPATH=$(pwd)
    conda activate chan
    python -m streamlit run src/moyan/web/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false &
    
    sleep 5
    print_message "✅ 本地服务已启动！" $GREEN
    print_message "📊 访问地址: http://localhost:8501" $BLUE
fi
