# 快速开始指南

欢迎使用墨岩缠论分析系统！本指南将帮助您快速上手使用系统进行股票技术分析。

## 🎯 系统简介

墨岩缠论分析系统是基于CZSC核心库构建的专业股票技术分析工具，支持：

- 🎯 **缠论技术分析**: 分型、笔、线段、背驰、买卖点识别
- 📈 **多时间周期**: 15分钟、30分钟、1小时、日线、周线、月线
- 📊 **MACD指标**: 深度集成MACD技术指标分析
- 🖥️ **Mac优化**: 专门针对Mac高DPI显示器优化
- 📄 **专业报告**: 自动生成Markdown格式分析报告

## 🚀 5分钟快速体验

### 1. 环境要求

```bash
# Python版本要求
Python >= 3.10

# 推荐使用conda管理环境
conda --version
```

### 2. 安装系统

```bash
# 克隆或下载项目
cd moyan-project

# 创建虚拟环境 (推荐)
conda create -n moyan python=3.11 -y
conda activate moyan

# 安装系统
pip install -e .
```

### 3. 验证安装

```bash
# 查看系统信息
moyan info

# 应该看到类似输出：
# ✅ CZSC核心库已加载: v0.10.2
# 🎯 墨岩缠论分析系统
# 📊 版本: 1.0.0
```

### 4. 第一次分析

```bash
# 分析东方锆业 (日线)
moyan analyze 002167

# 分析完成后会生成：
# 📊 002167_czsc_analysis.png  (可视化图表)
# 📄 002167_czsc_report.md     (分析报告)
```

### 5. 查看结果

分析完成后，您会在当前目录看到两个文件：

- **📊 图表文件**: `002167_czsc_analysis.png` - 包含K线、分型、笔、MACD等完整可视化
- **📄 报告文件**: `002167_czsc_report.md` - 详细的分析报告和投资建议

## 📈 基础使用示例

### 单股分析

```bash
# 基础分析 (默认日线)
moyan analyze 300308

# 指定K线级别
moyan analyze 300308 --kline 15m    # 15分钟线
moyan analyze 300308 --kline 30m    # 30分钟线
moyan analyze 300308 --kline 1h     # 1小时线
moyan analyze 300308 --kline 1d     # 日线
moyan analyze 300308 --kline 1wk    # 周线

# 指定时间区间
moyan analyze 300308 --start 20250101 --end 20250930
```

### 批量分析

```bash
# 批量分析多只股票
moyan batch 002167,300308,601138

# 批量分析指定K线级别
moyan batch 002167,300308,601138 --kline 15m
```

### 程序化使用

```python
from moyan import MoyanAnalyzer

# 创建分析器
analyzer = MoyanAnalyzer(kline_level="1d")

# 执行分析
result = analyzer.analyze("002167")

# 获取分析摘要
summary = analyzer.get_analysis_summary(result)
print(f"当前价格: {summary['current_price']}")
print(f"趋势状态: {summary['trend_status']}")
```

## 📊 支持的K线级别

| 级别代码 | 级别名称 | 默认天数 | 适用场景 |
|---------|---------|---------|---------|
| `15m` | 15分钟线 | 30天 | 短线交易，精细化分析 |
| `30m` | 30分钟线 | 60天 | 日内交易，平衡细节趋势 |
| `1h` | 1小时线 | 120天 | 短中线交易 |
| `1d` | 日线 | 365天 | 中长线分析，经典级别 |
| `1wk` | 周线 | 3年 | 长线投资，大级别格局 |
| `1mo` | 月线 | 5年 | 超长线分析 |

## 🎨 输出文件说明

### 可视化图表

生成的PNG图表包含以下内容：

1. **📈 主图**: K线图 + 分型标记 + 笔线段
2. **📊 成交量**: 成交量柱状图
3. **📈 MACD**: MACD线、信号线、柱状图
4. **🎯 买卖点**: 第一、二、三类买卖点标记
5. **📊 中枢**: 中枢区域标识
6. **⚠️ 背驰**: 背驰信号提示

### 分析报告

生成的Markdown报告包含：

1. **📋 基本信息**: 股票代码、名称、分析时间
2. **📊 技术指标**: 分型、笔、线段统计
3. **🎯 买卖点**: 详细的买卖点列表
4. **📈 趋势分析**: 当前趋势状态判断
5. **💡 投资建议**: 基于分析的投资建议
6. **⚠️ 风险提示**: 重要的风险提醒

## 🔧 常用命令

```bash
# 查看帮助
moyan --help
moyan analyze --help

# 查看系统信息
moyan info

# 检查依赖
moyan info --check-deps

# 启动Web界面 (如果已安装streamlit)
moyan web
```

## ⚠️ 注意事项

### 数据来源
- 系统使用yfinance获取股票数据
- 支持A股主要股票代码 (6位数字)
- 数据可能有延迟，请注意时效性

### 分析结果
- 分析结果仅供参考，不构成投资建议
- 请结合基本面分析和市场环境综合判断
- 建议设置合理止损，控制投资风险

### 系统要求
- 需要稳定的网络连接获取数据
- Mac用户可享受高DPI优化显示效果
- 推荐使用虚拟环境避免依赖冲突

## 🆘 遇到问题？

### 常见问题

1. **安装失败**: 检查Python版本是否>=3.10
2. **数据获取失败**: 检查网络连接和股票代码
3. **图表显示异常**: 确认matplotlib正确安装

### 获取帮助

- 📖 查看 [FAQ文档](../faq.md)
- 🐛 提交 [GitHub Issue](https://github.com/waditu/czsc/issues)
- 💬 参与社区讨论

## 🎉 下一步

恭喜！您已经完成了墨岩系统的快速入门。接下来您可以：

1. 📖 阅读 [详细教程](tutorial.md) 学习高级功能
2. 🔧 查看 [配置说明](../developer_guide/configuration.md) 自定义系统
3. 📊 了解 [缠论原理](../technical/algorithms.md) 深入理解分析逻辑
4. 🚀 探索 [API接口](../developer_guide/api_reference.md) 进行程序化开发

---

**开始您的缠论分析之旅吧！** 🚀
