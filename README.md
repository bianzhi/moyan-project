# 墨岩缠论分析系统 (Moyan CZSC Analysis System)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![CZSC Version](https://img.shields.io/badge/czsc-0.9.8%2B-green.svg)](https://github.com/waditu/czsc)
[![Streamlit](https://img.shields.io/badge/streamlit-1.50%2B-red.svg)](https://streamlit.io/)

## 📊 项目简介

墨岩缠论分析系统是基于**CZSC核心库**构建的专业股票技术分析应用平台。

### 🌟 核心特色

- **🎯 专业分析**: 完整的缠论技术分析体系（分型、笔、线段、背驰、买卖点）
- **📊 多时间周期**: 支持15分钟、30分钟、1小时、日线、周线、月线分析
- **🖥️ Web界面**: 基于Streamlit的专业Web分析界面
- **📈 交互图表**: 基于Plotly的高性能交互式可视化
- **⚡ 实时分析**: 基于yfinance获取最新股票数据
- **📁 智能输出**: 带时间戳的文件管理和目录组织

## 🚀 快速开始

### 安装步骤

1. **创建虚拟环境**
   ```bash
   conda create -n moyan_env python=3.11 -y
   conda activate moyan_env
   ```

2. **安装依赖**
   ```bash
   pip install -e .
   ```

3. **验证安装**
   ```bash
   moyan info
   ```

## 💻 使用方法

### 🌐 Web界面 (推荐)

```bash
# 启动Web界面
moyan web

# 访问地址: http://localhost:8501
```

#### Web功能特色

- **📊 直观参数配置**: 股票代码、K线级别、时间周期
- **🎨 可视化选项控制**: 可选择显示/隐藏各种技术要素
- **📈 交互式图表**: 高性能缩放、平移、悬停查看
- **📋 详细分析报告**: 多标签页展示完整分析结果

### 命令行界面 (CLI)

```bash
# 分析单只股票
moyan analyze 002167 --kline 1d

# 批量分析
moyan batch "002167,300308,601138" --kline 1d --days 120
```

## 📚 文档

- **[🌐 Web界面使用指南](docs/web_interface_guide.md)** - 详细的Web界面操作指南
- [快速开始指南](docs/user_guide/quick_start.md)
- [CLI命令参考](docs/user_guide/cli_reference.md)
- [CZSC集成指南](docs/CZSC_INTEGRATION_GUIDE.md)

## 🌟 功能亮点

### 缠论核心要素完整支持
- ✅ **分型识别**: 自动识别顶分型▼和底分型▲
- ✅ **笔的构建**: 蓝色向上笔、橙色向下笔
- ✅ **线段分析**: 紫色虚线显示
- ✅ **中枢识别**: 紫色半透明区域
- ✅ **背驰检测**: ⚠️警告标记
- ✅ **买卖点**: 第一、二、三类买卖点识别

### Web界面技术要素
| 类别 | 要素 | 说明 |
|------|------|------|
| **基础要素** | K线图 | 红涨绿跌，交互式缩放 |
| | 成交量 | 红绿柱状图 |
| | 移动平均线 | MA5、MA20 |
| **缠论要素** | 分型标记 | 顶分型▼、底分型▲ |
| | 笔和线段 | 笔连线、线段虚线 |
| | 买卖点 | 三类买卖点，不同颜色区分 |
| | 中枢和背驰 | 区域显示、警告标记 |
| **技术指标** | MACD | MACD线、信号线、柱状图 |
| | RSI | 相对强弱指标 |

## ⚠️ 重要声明

- **技术分析工具**: 本系统仅供技术分析学习和研究使用
- **投资风险**: 股市有风险，投资需谨慎

## 🔍 技术栈

- **核心算法**: [CZSC](https://github.com/waditu/czsc) - 缠论技术分析核心库
- **数据获取**: [yfinance](https://github.com/ranaroussi/yfinance) - 免费股票数据
- **Web界面**: [Streamlit](https://streamlit.io/) - 快速Web应用开发
- **交互图表**: [Plotly](https://plotly.com/) - 高性能可视化

---

<div align="center">
  <h3>🎯 墨岩缠论分析系统</h3>
  <p><em>专业 • 高效 • 易用</em></p>
  <p><strong>🌐 Web界面 | 📊 专业分析 | ⚡ 实时数据</strong></p>
</div>
