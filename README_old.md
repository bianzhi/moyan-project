# 墨岩缠论分析系统 (Moyan CZSC Analysis System)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![CZSC Version](https://img.shields.io/badge/czsc-0.9.8%2B-green.svg)](https://github.com/waditu/czsc)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 📊 项目简介

墨岩缠论分析系统是基于**CZSC核心库**构建的专业股票技术分析应用平台。系统采用**模块化架构设计**，将CZSC作为独立的核心库引用，实现了应用层与核心算法的完全分离。

### 🎯 设计理念

- **📚 核心库分离**: CZSC作为独立的技术分析核心库，专注算法实现
- **🚀 应用层专注**: Moyan专注于用户体验和应用功能实现  
- **🔄 版本同步**: 自动跟踪CZSC库更新，保持算法最新
- **🎨 功能扩展**: 在CZSC基础上构建丰富的应用层功能

## 🏗️ 项目架构

```
moyan-project/
├── src/moyan/                  # 核心源码
│   ├── core/                   # 核心模块
│   │   ├── __init__.py
│   │   ├── analyzer.py         # 分析引擎
│   │   └── data_source.py      # 数据源管理
│   ├── analyzer/               # 分析器模块
│   │   ├── __init__.py
│   │   ├── auto_analyzer.py    # 自动分析器
│   │   ├── multi_timeframe.py  # 多时间周期分析
│   │   └── strategy_analyzer.py # 策略分析器
│   ├── web/                    # Web界面模块
│   │   ├── __init__.py
│   │   ├── streamlit_app.py    # Streamlit应用
│   │   └── dashboard.py        # 仪表板
│   ├── cli/                    # 命令行模块
│   │   ├── __init__.py
│   │   ├── main.py            # CLI主入口
│   │   └── commands.py        # 命令实现
│   ├── utils/                  # 工具模块
│   │   ├── __init__.py
│   │   ├── visualization.py    # 可视化工具
│   │   └── report.py          # 报告生成
│   └── config/                 # 配置模块
│       ├── __init__.py
│       ├── settings.py        # 系统配置
│       └── kline_config.py    # K线配置
├── tests/                      # 测试代码
├── docs/                       # 文档
├── examples/                   # 示例代码
├── scripts/                    # 脚本工具
├── pyproject.toml             # 项目配置
├── requirements.txt           # 依赖管理
└── README.md                  # 项目说明
```

## ✨ 核心功能

### 🎯 缠论技术分析
- **分型识别**: 基于CZSC的顶分型和底分型识别
- **笔构建**: 向上笔和向下笔的自动构建
- **线段分析**: 线段识别和统计分析
- **背驰检测**: 顶背驰和底背驰信号识别
- **买卖点**: 第一、二、三类买卖点识别
- **中枢分析**: 中枢区域标识和分析

### 📈 多时间周期支持
- **15分钟线**: 短线交易分析，默认30天数据
- **30分钟线**: 日内交易分析，默认60天数据  
- **日线**: 中长线分析，默认365天数据
- **周线**: 长线投资分析，默认3年数据

### 📊 MACD技术指标
- **MACD线**: 12日EMA - 26日EMA (蓝色)
- **Signal线**: MACD的9日EMA (红色)
- **柱状图**: MACD - Signal (红绿柱)
- **零轴线**: 多空分界参考线

### 🖥️ Mac高DPI优化
- **分辨率**: 4770×3690像素 (Mac Retina优化)
- **DPI设置**: 200创建 + 300保存
- **字体渲染**: 10pt高清显示
- **线条优化**: 1.5pt细腻清晰

## 🚀 快速开始

### 环境要求
```bash
Python >= 3.10
CZSC >= 0.9.8
```

### 安装方式

#### 方法一: 从源码安装 (推荐开发者)
```bash
# 克隆项目
git clone <moyan-project-url>
cd moyan-project

# 创建虚拟环境
conda create -n moyan python=3.11 -y
conda activate moyan

# 安装依赖
pip install -e .
```

#### 方法二: 使用pip安装 (推荐用户)
```bash
pip install moyan
```

### 基础使用

#### 📱 命令行分析
```bash
# 基础分析 (默认日线)
moyan-analyze 002167

# 指定K线级别
moyan-analyze 002167 --kline 15m --start 20250801 --end 20250928

# 批量分析
moyan-analyze 002167,300308,601138 --kline 1d
```

#### 🖥️ Web界面
```bash
# 启动Web界面
moyan-web

# 或使用Streamlit
streamlit run src/moyan/web/streamlit_app.py
```

#### 🔧 程序化调用
```python
from moyan import MoyanAnalyzer

# 创建分析器
analyzer = MoyanAnalyzer(kline_level="15m")

# 运行分析
result = analyzer.analyze("002167", start_date="20250801", end_date="20250928")

# 生成报告
analyzer.generate_report(result)
```

## 📊 与CZSC的关系

### 🔗 依赖关系
```python
# Moyan依赖CZSC核心库
import czsc
from czsc import CZSC, CzscTrader, RawBar

# Moyan在CZSC基础上构建应用层
class MoyanAnalyzer:
    def __init__(self):
        self.czsc_engine = CZSC()  # 使用CZSC核心
```

### 🔄 版本同步策略
- **自动更新**: 定期检查CZSC库更新
- **版本锁定**: 在pyproject.toml中指定CZSC版本范围
- **兼容性测试**: 每次更新后运行完整测试套件
- **回滚机制**: 如有问题可快速回滚到稳定版本

### 📈 功能分工
| 组件 | CZSC核心库 | Moyan应用层 |
|------|-----------|------------|
| **算法实现** | ✅ 缠论算法核心 | ❌ 不重复实现 |
| **数据结构** | ✅ RawBar, CZSC等 | ❌ 直接使用 |
| **用户界面** | ❌ 专注算法 | ✅ CLI, Web界面 |
| **可视化** | ❌ 基础功能 | ✅ 高级可视化 |
| **报告生成** | ❌ 不涉及 | ✅ 专业报告 |
| **配置管理** | ❌ 基础配置 | ✅ 应用配置 |

## 🎨 技术栈

| 技术层次 | 使用技术 |
|---------|---------|
| **核心算法** | CZSC (缠论核心库) |
| **用户界面** | CLI + Streamlit + Web |
| **数据获取** | yfinance + 可扩展数据源 |
| **可视化** | matplotlib + plotly (Mac优化) |
| **数据处理** | pandas + numpy |
| **配置管理** | TOML + 分层配置 |
| **测试框架** | pytest + 自动化测试 |
| **文档生成** | Markdown + 自动化报告 |

## 🔧 开发指南

### 本地开发
```bash
# 克隆项目
git clone <moyan-project-url>
cd moyan-project

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black src/ tests/
isort src/ tests/

# 类型检查
mypy src/
```

### CZSC库更新流程
```bash
# 检查CZSC更新
pip list --outdated | grep czsc

# 更新CZSC
pip install --upgrade czsc

# 运行兼容性测试
pytest tests/test_czsc_compatibility.py

# 如有问题，回滚版本
pip install czsc==0.9.8
```

## 📚 文档和示例

- **📖 用户手册**: [docs/user_guide.md](docs/user_guide.md)
- **🔧 开发文档**: [docs/developer_guide.md](docs/developer_guide.md)
- **💡 示例代码**: [examples/](examples/)
- **🧪 测试用例**: [tests/](tests/)

## ⚠️ 重要说明

### 投资风险提示
- 本系统基于缠论技术分析，仅供参考，不构成投资建议
- 股市有风险，投资需谨慎
- 请结合基本面分析和市场环境综合判断
- 建议设置合理止损，控制投资风险

### 技术说明
- 系统依赖CZSC核心库，请确保版本兼容性
- Mac用户可享受高DPI优化显示效果
- 支持A股主要股票代码 (6位数字)
- 数据来源于yfinance，请注意数据延迟

## 🤝 贡献指南

欢迎贡献代码和建议！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- **CZSC项目**: 感谢提供强大的缠论分析核心库
- **开源社区**: 感谢各种优秀的Python库支持
- **用户反馈**: 感谢用户的宝贵意见和建议

---

**墨岩缠论分析系统** - 让技术分析更专业，让投资决策更准确！

🎉 **基于CZSC + 应用层创新 = 专业级技术分析平台**
