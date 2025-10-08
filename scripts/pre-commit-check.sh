#!/bin/bash

# Git提交前检查脚本 - 防止大文件提交
# Pre-commit check script - Prevent large files from being committed

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_message() {
    echo -e "${2}${1}${NC}"
}

print_message "🔍 Git提交前检查..." $BLUE
print_message "==================" $BLUE

# 检查是否有大文件被暂存
print_message "📋 检查暂存区大文件..." $YELLOW

large_files_found=false

# 检查暂存区中的文件
for file in $(git diff --cached --name-only); do
    if [ -f "$file" ]; then
        size=$(wc -c < "$file" 2>/dev/null || echo 0)
        size_mb=$((size / 1024 / 1024))
        
        if [ $size_mb -gt 10 ]; then
            print_message "❌ 发现大文件: $file (${size_mb}MB)" $RED
            large_files_found=true
        fi
    fi
done

# 检查特定的Docker文件
docker_files=(
    "*.tar"
    "*.tar.gz" 
    "*.tar.bz2"
    "*-docker.tar"
    "moyan-czsc-docker.tar"
)

print_message "🐳 检查Docker相关文件..." $YELLOW

for pattern in "${docker_files[@]}"; do
    if git diff --cached --name-only | grep -q "$pattern" 2>/dev/null; then
        print_message "❌ 发现Docker文件: $pattern" $RED
        large_files_found=true
    fi
done

# 检查输出目录
output_dirs=(
    "output/"
    "outputs/"
    "logs/"
    "charts/"
    "reports/"
)

print_message "📁 检查输出目录..." $YELLOW

for dir in "${output_dirs[@]}"; do
    if git diff --cached --name-only | grep -q "^$dir" 2>/dev/null; then
        print_message "⚠️  发现输出目录文件: $dir" $YELLOW
        print_message "💡 建议: 输出文件通常不需要提交到Git" $YELLOW
    fi
done

# 检查敏感配置文件
sensitive_files=(
    "*.env"
    "**/config/local_*"
    "**/config/secret_*"
    "config/local_config.py"
    "config/secret_config.py"
)

print_message "🔐 检查敏感配置文件..." $YELLOW

for pattern in "${sensitive_files[@]}"; do
    if git diff --cached --name-only | grep -q "$pattern" 2>/dev/null; then
        print_message "⚠️  发现敏感配置: $pattern" $YELLOW
        print_message "💡 建议: 检查是否包含敏感信息" $YELLOW
    fi
done

# 总结
print_message "" $NC
if [ "$large_files_found" = true ]; then
    print_message "❌ 检查失败：发现不应该提交的大文件！" $RED
    print_message "" $NC
    print_message "💡 解决方案：" $YELLOW
    print_message "1. 将大文件添加到 .gitignore" $NC
    print_message "2. 使用 git reset HEAD <file> 取消暂存" $NC
    print_message "3. 使用云存储分享大文件" $NC
    print_message "4. 参考 DOCKER_DISTRIBUTION.md 了解分发方式" $NC
    print_message "" $NC
    exit 1
else
    print_message "✅ 检查通过：没有发现问题文件" $GREEN
    print_message "" $NC
    
    # 显示即将提交的文件
    staged_files=$(git diff --cached --name-only | wc -l)
    if [ $staged_files -gt 0 ]; then
        print_message "📋 即将提交的文件 ($staged_files 个):" $BLUE
        git diff --cached --name-only | sed 's/^/  ✓ /'
        print_message "" $NC
    fi
    
    print_message "🎉 可以安全提交！" $GREEN
fi
