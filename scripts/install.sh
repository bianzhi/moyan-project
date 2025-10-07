#!/bin/bash
# 墨岩缠论分析系统安装脚本
# Moyan CZSC Analysis System Installation Script

set -e  # 遇到错误立即退出

echo "🎯 墨岩缠论分析系统安装脚本"
echo "=================================="
echo ""

# 检查Python版本
echo "🔍 检查Python环境..."
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.10"

if (( $(echo "$PYTHON_VERSION < $REQUIRED_VERSION" | bc -l) )); then
    echo "❌ Python版本过低。本系统需要Python $REQUIRED_VERSION或更高版本。"
    echo "当前版本: Python $PYTHON_VERSION"
    echo "请升级Python后重试。"
    exit 1
else
    echo "✅ 检测到Python $PYTHON_VERSION，符合要求。"
fi

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️ 建议在虚拟环境中安装，以避免污染系统Python环境。"
    read -p "是否现在创建一个名为 'moyan' 的conda虚拟环境并安装？(y/n): " CREATE_ENV
    if [[ "$CREATE_ENV" == "y" || "$CREATE_ENV" == "Y" ]]; then
        echo "🚀 正在创建conda虚拟环境 'moyan'..."
        conda create -n moyan python=3.11 -y
        if [ $? -ne 0 ]; then
            echo "❌ 创建conda环境失败。请确保conda已正确安装并配置。"
            exit 1
        fi
        echo "✅ conda环境 'moyan' 创建成功。请手动激活环境后再次运行此脚本："
        echo "   conda activate moyan"
        echo "   ./scripts/install.sh"
        exit 0
    else
        echo "继续在当前环境安装..."
    fi
else
    echo "✅ 已在虚拟环境 '$VIRTUAL_ENV' 中运行。"
fi

# 检查CZSC核心库
echo "📦 检查CZSC核心库..."
if python3 -c "import czsc" 2>/dev/null; then
    CZSC_VERSION=$(python3 -c "import czsc; print(getattr(czsc, '__version__', 'unknown'))")
    echo "✅ CZSC核心库已安装: v$CZSC_VERSION"
else
    echo "📥 CZSC核心库未安装，正在安装..."
    pip install czsc>=0.9.8
    if [ $? -ne 0 ]; then
        echo "❌ CZSC核心库安装失败。"
        exit 1
    fi
    echo "✅ CZSC核心库安装成功。"
fi

# 安装Moyan系统
echo "📦 正在安装Moyan系统..."

# 安装核心依赖
echo "📥 安装核心依赖..."
pip install -e .
if [ $? -ne 0 ]; then
    echo "❌ Moyan系统安装失败。"
    exit 1
fi

# 检查可选依赖
echo "🔍 检查可选依赖..."

# 检查Streamlit (Web界面)
if python3 -c "import streamlit" 2>/dev/null; then
    echo "✅ Streamlit已安装 (Web界面可用)"
else
    echo "⚠️ Streamlit未安装 (Web界面不可用)"
    read -p "是否安装Streamlit以启用Web界面？(y/n): " INSTALL_STREAMLIT
    if [[ "$INSTALL_STREAMLIT" == "y" || "$INSTALL_STREAMLIT" == "Y" ]]; then
        pip install streamlit plotly
        echo "✅ Streamlit安装完成。"
    fi
fi

# 检查TA-Lib (增强技术指标)
if python3 -c "import talib" 2>/dev/null; then
    echo "✅ TA-Lib已安装 (增强技术指标可用)"
else
    echo "⚠️ TA-Lib未安装 (增强技术指标不可用)"
    echo "💡 提示: TA-Lib需要单独安装，请参考官方文档"
fi

# 运行测试
echo "🧪 运行基础测试..."
python3 -c "
try:
    from moyan import MoyanAnalyzer, welcome
    welcome()
    print('✅ Moyan系统导入成功')
except Exception as e:
    print(f'❌ Moyan系统导入失败: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ 基础测试失败。"
    exit 1
fi

echo ""
echo "🎉 墨岩缠论分析系统安装成功！"
echo ""
echo "🚀 快速开始:"
echo "  # 命令行分析"
echo "  moyan analyze 002167"
echo ""
echo "  # Web界面"
echo "  moyan web"
echo ""
echo "  # 查看帮助"
echo "  moyan --help"
echo ""
echo "📚 更多信息:"
echo "  • 项目文档: README.md"
echo "  • 示例代码: examples/"
echo "  • 测试代码: tests/"
echo ""
echo "=================================="
