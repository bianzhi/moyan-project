#!/bin/bash
# -*- coding: utf-8 -*-
"""
CZSC自动更新脚本
Automatic CZSC update script for Moyan project
"""

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 函数定义
print_header() {
    echo -e "${CYAN}🔄 Moyan项目CZSC自动更新脚本${NC}"
    echo -e "${CYAN}===============================================${NC}"
    echo -e "📅 执行时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
}

print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_environment() {
    print_step "检查运行环境..."
    
    # 检查Python
    if ! command -v python &> /dev/null; then
        print_error "Python未安装或不在PATH中"
        exit 1
    fi
    
    # 检查pip
    if ! command -v pip &> /dev/null; then
        print_error "pip未安装或不在PATH中"
        exit 1
    fi
    
    # 检查是否在虚拟环境中
    if [[ -z "$VIRTUAL_ENV" && -z "$CONDA_DEFAULT_ENV" ]]; then
        print_warning "未检测到虚拟环境，建议在虚拟环境中运行"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "操作已取消"
            exit 1
        fi
    else
        if [[ -n "$CONDA_DEFAULT_ENV" ]]; then
            print_success "检测到conda环境: $CONDA_DEFAULT_ENV"
        elif [[ -n "$VIRTUAL_ENV" ]]; then
            print_success "检测到虚拟环境: $(basename $VIRTUAL_ENV)"
        fi
    fi
}

get_current_version() {
    print_step "获取当前CZSC版本..."
    CURRENT_VERSION=$(pip show czsc 2>/dev/null | grep Version | cut -d' ' -f2 | tr -d '[:space:]' || echo "")
    
    if [[ -z "$CURRENT_VERSION" ]]; then
        print_error "未检测到已安装的CZSC"
        echo "请先安装CZSC: pip install czsc"
        exit 1
    fi
    
    print_success "当前版本: $CURRENT_VERSION"
}

get_latest_version() {
    print_step "获取最新版本信息..."
    
    # 尝试从PyPI获取最新版本
    LATEST_VERSION=$(python -c "
import requests
try:
    response = requests.get('https://pypi.org/pypi/czsc/json', timeout=10)
    data = response.json()
    print(data['info']['version'])
except Exception as e:
    print('ERROR')
" 2>/dev/null)
    
    if [[ "$LATEST_VERSION" == "ERROR" || -z "$LATEST_VERSION" ]]; then
        print_error "无法获取最新版本信息"
        echo "请检查网络连接或稍后重试"
        exit 1
    fi
    
    print_success "最新版本: $LATEST_VERSION"
}

compare_versions() {
    print_step "比较版本..."
    
    # 使用Python比较版本
    VERSION_COMPARE=$(python -c "
from packaging import version
import sys
try:
    current = version.parse('$CURRENT_VERSION')
    latest = version.parse('$LATEST_VERSION')
    if current < latest:
        print('outdated')
    elif current > latest:
        print('ahead')
    else:
        print('latest')
except Exception:
    print('error')
")
    
    case $VERSION_COMPARE in
        "latest")
            print_success "已是最新版本，无需更新"
            return 1
            ;;
        "ahead")
            print_warning "当前版本比PyPI更新 (可能是开发版本)"
            return 1
            ;;
        "outdated")
            print_warning "发现新版本: $CURRENT_VERSION → $LATEST_VERSION"
            return 0
            ;;
        *)
            print_error "版本比较失败"
            return 1
            ;;
    esac
}

analyze_update_type() {
    print_step "分析更新类型..."
    
    UPDATE_TYPE=$(python -c "
from packaging import version
try:
    current = version.parse('$CURRENT_VERSION')
    latest = version.parse('$LATEST_VERSION')
    
    if latest.major > current.major:
        print('major')
    elif latest.minor > current.minor:
        print('minor')
    elif latest.micro > current.micro:
        print('patch')
    else:
        print('none')
except Exception:
    print('unknown')
")
    
    case $UPDATE_TYPE in
        "patch")
            print_success "补丁更新 (风险: 低) - 通常是bug修复"
            UPDATE_RISK="low"
            ;;
        "minor")
            print_warning "次要更新 (风险: 中等) - 新功能，通常向后兼容"
            UPDATE_RISK="medium"
            ;;
        "major")
            print_error "主要更新 (风险: 高) - 可能包含破坏性变更"
            UPDATE_RISK="high"
            ;;
        *)
            print_warning "无法确定更新类型"
            UPDATE_RISK="unknown"
            ;;
    esac
}

backup_environment() {
    print_step "备份当前环境..."
    
    BACKUP_FILE="requirements_backup_$(date +%Y%m%d_%H%M%S).txt"
    pip freeze > "$BACKUP_FILE"
    print_success "环境备份已保存: $BACKUP_FILE"
    
    # 保存当前CZSC版本
    echo "czsc==$CURRENT_VERSION" > czsc_rollback.txt
    print_success "回滚信息已保存: czsc_rollback.txt"
}

confirm_update() {
    echo ""
    echo -e "${PURPLE}📋 更新摘要:${NC}"
    echo "   当前版本: $CURRENT_VERSION"
    echo "   目标版本: $LATEST_VERSION"
    echo "   更新类型: $UPDATE_TYPE"
    echo "   风险级别: $UPDATE_RISK"
    echo ""
    
    if [[ "$UPDATE_RISK" == "high" ]]; then
        echo -e "${RED}⚠️ 警告: 这是一个主要版本更新，可能包含破坏性变更！${NC}"
        echo "建议先在测试环境中验证兼容性"
        echo ""
    fi
    
    if [[ "$1" != "--auto" ]]; then
        read -p "是否继续更新? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "更新已取消"
            exit 0
        fi
    else
        print_warning "自动模式: 跳过确认"
    fi
}

perform_update() {
    print_step "开始更新CZSC..."
    
    if pip install --upgrade czsc; then
        print_success "CZSC更新完成"
        
        # 获取新版本
        NEW_VERSION=$(pip show czsc | grep Version | cut -d' ' -f2 | tr -d '[:space:]')
        print_success "新版本: $NEW_VERSION"
    else
        print_error "CZSC更新失败"
        return 1
    fi
}

run_tests() {
    print_step "运行兼容性测试..."
    
    # 基础导入测试
    echo "🧪 测试基础导入..."
    if python -c "import czsc; from czsc import CZSC, RawBar; print('✅ 基础导入测试通过')" 2>/dev/null; then
        print_success "基础导入测试通过"
    else
        print_error "基础导入测试失败"
        return 1
    fi
    
    # 如果存在测试文件，运行测试
    if [[ -f "tests/test_basic.py" ]]; then
        echo "🧪 运行基础功能测试..."
        if python tests/test_basic.py; then
            print_success "基础功能测试通过"
        else
            print_error "基础功能测试失败"
            return 1
        fi
    fi
    
    # 简单的分析测试 (如果是自动模式则跳过)
    if [[ "$1" != "--auto" ]]; then
        echo "🧪 运行简单分析测试..."
        if timeout 60 python -c "
from moyan import MoyanAnalyzer
try:
    analyzer = MoyanAnalyzer(kline_level='1d')
    # 只测试创建，不执行实际分析
    print('✅ 分析器创建测试通过')
except Exception as e:
    print(f'❌ 分析器测试失败: {e}')
    exit(1)
"; then
            print_success "分析器测试通过"
        else
            print_warning "分析器测试失败或超时"
            return 1
        fi
    fi
    
    return 0
}

handle_test_failure() {
    print_error "兼容性测试失败！"
    echo ""
    echo -e "${YELLOW}🔄 回滚选项:${NC}"
    echo "1. 立即回滚到之前版本"
    echo "2. 保持新版本，稍后手动处理"
    echo "3. 退出脚本"
    echo ""
    
    read -p "请选择 (1-3): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            print_step "回滚到之前版本..."
            if [[ -f "czsc_rollback.txt" ]]; then
                if pip install -r czsc_rollback.txt; then
                    print_success "回滚成功"
                    # 清理回滚文件
                    rm -f czsc_rollback.txt
                else
                    print_error "回滚失败"
                fi
            else
                print_error "找不到回滚信息文件"
            fi
            ;;
        2)
            print_warning "保持新版本，请手动检查兼容性问题"
            echo "💡 回滚命令: pip install czsc==$CURRENT_VERSION"
            ;;
        3)
            echo "退出脚本"
            ;;
    esac
}

cleanup() {
    # 清理临时文件 (保留备份文件)
    if [[ -f "czsc_rollback.txt" ]]; then
        rm -f czsc_rollback.txt
    fi
}

show_help() {
    echo "CZSC自动更新脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --auto          自动模式，跳过所有确认"
    echo "  --check-only    仅检查版本，不执行更新"
    echo "  --force         强制更新，即使版本相同"
    echo "  --help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                    # 交互式更新"
    echo "  $0 --check-only      # 仅检查版本"
    echo "  $0 --auto            # 自动更新"
    echo ""
}

# 主程序
main() {
    # 解析命令行参数
    AUTO_MODE=false
    CHECK_ONLY=false
    FORCE_UPDATE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --auto)
                AUTO_MODE=true
                shift
                ;;
            --check-only)
                CHECK_ONLY=true
                shift
                ;;
            --force)
                FORCE_UPDATE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 执行主要流程
    print_header
    check_environment
    get_current_version
    get_latest_version
    
    if [[ "$CHECK_ONLY" == true ]]; then
        compare_versions || true
        echo ""
        echo "🔗 更多信息:"
        echo "   📋 GitHub: https://github.com/waditu/czsc"
        echo "   📦 PyPI: https://pypi.org/project/czsc/"
        echo "   📖 更新指南: docs/developer_guide/czsc_update_guide.md"
        exit 0
    fi
    
    if [[ "$FORCE_UPDATE" == false ]]; then
        if ! compare_versions; then
            exit 0
        fi
    fi
    
    analyze_update_type
    backup_environment
    
    if [[ "$AUTO_MODE" == true ]]; then
        confirm_update "--auto"
    else
        confirm_update
    fi
    
    if perform_update; then
        if [[ "$AUTO_MODE" == true ]]; then
            if run_tests "--auto"; then
                print_success "🎉 自动更新成功完成!"
                cleanup
            else
                handle_test_failure
            fi
        else
            if run_tests; then
                print_success "🎉 更新成功完成!"
                cleanup
            else
                handle_test_failure
            fi
        fi
    else
        print_error "更新失败，请检查错误信息"
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}📚 更新完成后建议:${NC}"
    echo "1. 查看更新日志: https://github.com/waditu/czsc/releases"
    echo "2. 运行完整测试: pytest tests/"
    echo "3. 更新文档: docs/developer_guide/czsc_update_guide.md"
}

# 捕获退出信号，确保清理
trap cleanup EXIT

# 执行主程序
main "$@"
