# 安装指南

本指南将详细说明如何在不同环境中安装墨岩缠论分析系统。

## 📋 系统要求

### 基础要求
- **Python**: >= 3.10 (推荐 3.11)
- **操作系统**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **内存**: 至少 4GB RAM (推荐 8GB+)
- **存储**: 至少 2GB 可用空间
- **网络**: 稳定的互联网连接 (用于获取股票数据)

### 推荐环境
- **Python**: 3.11
- **包管理器**: conda (Anaconda/Miniconda)
- **IDE**: VS Code, PyCharm, Jupyter Lab
- **显示器**: Mac Retina显示器 (享受高DPI优化)

## 🚀 安装方法

### 方法一: 开发模式安装 (推荐)

适合开发者和高级用户，可以修改源码和获得最新功能。

```bash
# 1. 克隆或下载项目
git clone <moyan-project-url>
cd moyan-project

# 2. 创建虚拟环境
conda create -n moyan python=3.11 -y
conda activate moyan

# 3. 安装项目
pip install -e .

# 4. 验证安装
moyan info
```

### 方法二: 包安装 (未来支持)

```bash
# 直接从PyPI安装 (未来版本)
pip install moyan

# 或从GitHub安装
pip install git+https://github.com/your-org/moyan-project.git
```

### 方法三: 使用安装脚本

```bash
# 运行自动安装脚本
cd moyan-project
chmod +x scripts/install.sh
./scripts/install.sh
```

## 🐍 Python环境管理

### 使用Conda (推荐)

```bash
# 安装Miniconda (如果尚未安装)
# 下载地址: https://docs.conda.io/en/latest/miniconda.html

# 创建专用环境
conda create -n moyan python=3.11 -y

# 激活环境
conda activate moyan

# 验证Python版本
python --version  # 应该显示 Python 3.11.x
```

### 使用venv

```bash
# 创建虚拟环境
python3.11 -m venv moyan_env

# 激活环境 (Linux/Mac)
source moyan_env/bin/activate

# 激活环境 (Windows)
moyan_env\Scripts\activate

# 验证环境
which python  # 应该指向虚拟环境中的python
```

## 📦 依赖安装

### 核心依赖

系统会自动安装以下核心依赖：

```
czsc>=0.9.8                    # CZSC缠论核心库
pandas>=1.5.0                  # 数据处理
numpy>=1.21.0                  # 数值计算
matplotlib>=3.5.0              # 图表绘制
yfinance>=0.2.0                # 股票数据获取
requests>=2.28.0               # HTTP请求
loguru>=0.6.0                  # 日志管理
```

### 可选依赖

```bash
# Web界面支持
pip install streamlit plotly

# 增强技术指标
pip install ta-lib  # 需要单独安装，见下方说明

# 专业K线图
pip install mplfinance

# 统计图表
pip install seaborn
```

### TA-Lib安装 (可选)

TA-Lib提供更多技术指标，但安装较复杂：

#### macOS
```bash
# 使用Homebrew
brew install ta-lib
pip install ta-lib

# 或使用conda
conda install -c conda-forge ta-lib
```

#### Ubuntu/Debian
```bash
# 安装系统依赖
sudo apt-get install build-essential
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install

# 安装Python包
pip install ta-lib
```

#### Windows
```bash
# 下载预编译包
pip install --find-links https://www.lfd.uci.edu/~gohlke/pythonlibs/ TA-Lib
```

## 🌍 网络配置

### 国内用户加速

```bash
# 配置pip镜像源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/

# 或临时使用镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ -e .
```

### 代理设置

```bash
# 如果需要使用代理
export http_proxy=http://proxy.company.com:8080
export https_proxy=http://proxy.company.com:8080

# 或在pip命令中指定
pip install --proxy http://proxy.company.com:8080 -e .
```

## 🔧 安装验证

### 基础验证

```bash
# 检查Python版本
python --version

# 检查Moyan安装
moyan --version

# 查看系统信息
moyan info

# 检查依赖
moyan info --check-deps
```

### 功能验证

```bash
# 测试分析功能
moyan analyze 000001 --kline 1d

# 应该成功生成分析文件
ls -la 000001_*
```

### 运行测试

```bash
# 运行基础测试
python tests/test_basic.py

# 运行完整测试套件 (如果安装了pytest)
pytest tests/
```

## 🐛 常见安装问题

### Python版本问题

```bash
# 错误: Python版本过低
❌ Python版本过低。本系统需要Python 3.10或更高版本。

# 解决方案
conda install python=3.11
# 或重新创建环境
conda create -n moyan python=3.11 -y
```

### 依赖冲突

```bash
# 错误: 包版本冲突
❌ ERROR: pip's dependency resolver does not currently consider all the ways...

# 解决方案1: 使用新环境
conda create -n moyan_clean python=3.11 -y
conda activate moyan_clean

# 解决方案2: 强制重装
pip install --force-reinstall -e .
```

### 网络问题

```bash
# 错误: 网络连接超时
❌ ReadTimeoutError: HTTPSConnectionPool...

# 解决方案1: 使用镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ -e .

# 解决方案2: 增加超时时间
pip install --timeout 300 -e .
```

### CZSC安装失败

```bash
# 错误: CZSC核心库安装失败
❌ ERROR: Could not find a version that satisfies the requirement czsc>=0.9.8

# 解决方案1: 更新pip
pip install --upgrade pip

# 解决方案2: 手动安装CZSC
pip install czsc>=0.9.8

# 解决方案3: 从GitHub安装
pip install git+https://github.com/waditu/czsc.git
```

### 权限问题

```bash
# 错误: 权限不足
❌ PermissionError: [Errno 13] Permission denied

# 解决方案1: 使用用户安装
pip install --user -e .

# 解决方案2: 使用虚拟环境 (推荐)
conda create -n moyan python=3.11 -y
conda activate moyan
```

## 🔄 更新和卸载

### 更新系统

```bash
# 更新到最新版本
cd moyan-project
git pull  # 如果是从git克隆的
pip install -e . --upgrade

# 更新CZSC核心库
pip install --upgrade czsc
```

### 卸载系统

```bash
# 卸载Moyan
pip uninstall moyan

# 删除虚拟环境
conda remove -n moyan --all

# 或删除整个项目目录
rm -rf moyan-project/
```

## 🎯 不同环境的安装

### 开发环境

```bash
# 完整开发环境
conda create -n moyan_dev python=3.11 -y
conda activate moyan_dev
pip install -e ".[dev]"  # 包含开发依赖

# 安装开发工具
pip install black isort flake8 mypy pytest
```

### 生产环境

```bash
# 最小化生产环境
conda create -n moyan_prod python=3.11 -y
conda activate moyan_prod
pip install -e .  # 只安装核心依赖
```

### Docker环境

```dockerfile
# Dockerfile示例
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .

CMD ["moyan", "info"]
```

## 📞 获取帮助

如果安装过程中遇到问题：

1. **查看错误信息**: 仔细阅读错误提示
2. **检查环境**: 确认Python版本和虚拟环境
3. **查看日志**: 使用 `pip install -v` 查看详细日志
4. **搜索问题**: 在GitHub Issues中搜索类似问题
5. **提交Issue**: 如果问题未解决，请提交详细的错误报告

---

**安装成功后，您就可以开始使用墨岩缠论分析系统了！** 🎉

下一步: 查看 [快速开始指南](quick_start.md) 学习基本使用方法。
