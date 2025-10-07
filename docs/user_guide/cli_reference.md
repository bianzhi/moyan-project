# CLI命令参考

墨岩缠论分析系统提供了完整的命令行界面，本文档详细介绍所有可用的CLI命令。

## 📋 命令概览

```bash
moyan <command> [options]
```

### 可用命令

| 命令 | 描述 | 示例 |
|------|------|------|
| `info` | 显示系统信息 | `moyan info` |
| `analyze` | 分析单只股票 | `moyan analyze 002167` |
| `batch` | 批量分析多只股票 | `moyan batch 002167,300308` |
| `web` | 启动Web界面 | `moyan web` |

## 🔧 全局选项

```bash
moyan [global-options] <command> [command-options]
```

### 全局选项

- `--version`: 显示版本信息
- `--verbose, -v`: 显示详细输出
- `--config <file>`: 指定配置文件路径
- `--help, -h`: 显示帮助信息

### 示例

```bash
# 查看版本
moyan --version

# 详细输出模式
moyan --verbose analyze 002167

# 使用自定义配置
moyan --config my_config.toml analyze 002167
```

## 📊 info 命令

显示系统信息和依赖状态。

### 语法

```bash
moyan info [options]
```

### 选项

- `--check-deps`: 检查依赖库版本

### 示例

```bash
# 基本系统信息
moyan info

# 检查所有依赖
moyan info --check-deps
```

### 输出示例

```
======================================================================
🎯 墨岩缠论分析系统
======================================================================
📊 版本: 1.0.0
👥 作者: CZSC Community
📝 描述: 基于CZSC的专业股票技术分析应用平台

✨ 核心功能:
  • 缠论技术分析 (分型、笔、线段、背驰、买卖点)
  • 多时间周期支持 (15m/30m/1h/1d/1wk/1mo)
  • MACD技术指标集成
  • Mac高分辨率显示器优化
  • 专业级图表输出
  • 详细分析报告生成

📈 支持的K线级别:
  • 15m: 15分钟线 - 15分钟K线，适合短线交易
  • 30m: 30分钟线 - 30分钟K线，适合日内交易
  • 1h: 1小时线 - 1小时K线，适合短中线交易
  • 1d: 日线 - 日K线，适合中长线分析
  • 1wk: 周线 - 周K线，适合长线投资分析
  • 1mo: 月线 - 月K线，适合超长线分析
```

## 📈 analyze 命令

分析单只股票的缠论技术指标。

### 语法

```bash
moyan analyze <stock_code> [options]
```

### 参数

- `<stock_code>`: 6位股票代码 (必需)

### 选项

- `--kline, -k <level>`: K线级别 (默认: 1d)
- `--start, -s <date>`: 开始日期 (YYYYMMDD格式)
- `--end, -e <date>`: 结束日期 (YYYYMMDD格式)
- `--days, -d <number>`: 获取天数
- `--output, -o <dir>`: 输出目录

### K线级别

| 级别 | 名称 | 描述 |
|------|------|------|
| `15m` | 15分钟线 | 短线交易分析 |
| `30m` | 30分钟线 | 日内交易分析 |
| `1h` | 1小时线 | 短中线交易 |
| `1d` | 日线 | 中长线分析 (默认) |
| `1wk` | 周线 | 长线投资分析 |
| `1mo` | 月线 | 超长线分析 |

### 示例

```bash
# 基础分析 (默认日线)
moyan analyze 002167

# 指定K线级别
moyan analyze 002167 --kline 15m
moyan analyze 002167 -k 30m

# 指定时间区间
moyan analyze 002167 --start 20250101 --end 20250930
moyan analyze 002167 -s 20250101 -e 20250930

# 指定获取天数
moyan analyze 002167 --days 90
moyan analyze 002167 -d 90

# 指定输出目录
moyan analyze 002167 --output ./results
moyan analyze 002167 -o ./results

# 组合使用
moyan analyze 002167 --kline 15m --start 20250801 --end 20250928 --output ./analysis
```

### 输出文件

分析完成后会生成以下文件：

- `<stock_code>_czsc_analysis.png`: 可视化图表
- `<stock_code>_czsc_report.md`: 详细分析报告

### 输出示例

```
🚀 开始分析股票: 002167
📈 K线级别: 日线 (1d)
✅ 墨岩分析器已初始化
📈 K线级别: 日线 (1d)
🔧 CZSC版本: 0.10.2
📊 正在获取股票 002167 的数据...
📈 K线级别: 日线 (1d)
📅 时间区间: 2024-09-29 至 2025-09-29
✅ 成功获取 243 条日线数据
📈 股票名称: Guangdong Orient Zirconic Ind Sci & Tech Co.,Ltd
🔄 转换数据格式...
✅ 数据格式转换完成: 243 根K线
🧮 开始缠论分析...
✅ 缠论分析完成
🎨 生成可视化图表...
✅ 可视化图表已保存: 002167_czsc_analysis.png
📄 生成分析报告...
✅ 分析报告已保存: 002167_czsc_report.md
✅ 分析完成: 002167
```

## 📋 batch 命令

批量分析多只股票。

### 语法

```bash
moyan batch <stock_codes> [options]
```

### 参数

- `<stock_codes>`: 股票代码列表，用逗号分隔 (必需)

### 选项

- `--kline, -k <level>`: K线级别 (默认: 1d)
- `--start, -s <date>`: 开始日期 (YYYYMMDD格式)
- `--end, -e <date>`: 结束日期 (YYYYMMDD格式)
- `--output, -o <dir>`: 输出目录
- `--parallel, -p`: 并行处理 (实验性功能)

### 示例

```bash
# 基础批量分析
moyan batch 002167,300308,601138

# 指定K线级别
moyan batch 002167,300308,601138 --kline 15m

# 指定时间区间
moyan batch 002167,300308,601138 --start 20250101 --end 20250930

# 并行处理
moyan batch 002167,300308,601138 --parallel

# 组合使用
moyan batch 002167,300308,601138 -k 1d -s 20250101 -o ./batch_results
```

### 输出示例

```
🚀 开始批量分析 3 只股票
📈 K线级别: 1d
📋 股票列表: 002167, 300308, 601138

📊 进度: 1/3 - 分析 002167
✅ 002167 分析成功

📊 进度: 2/3 - 分析 300308
✅ 300308 分析成功

📊 进度: 3/3 - 分析 601138
✅ 601138 分析成功

🎉 批量分析完成: 3/3 成功

📋 详细结果:
  ✅ 002167: 价格=13.51, 趋势=空头趋势
  ✅ 300308: 价格=45.23, 趋势=多头趋势
  ✅ 601138: 价格=28.67, 趋势=震荡格局
```

## 🌐 web 命令

启动Streamlit Web界面 (需要安装streamlit)。

### 语法

```bash
moyan web [options]
```

### 选项

- `--port <number>`: Web服务端口 (默认: 8501)
- `--host <address>`: Web服务主机 (默认: localhost)

### 示例

```bash
# 使用默认设置
moyan web

# 指定端口
moyan web --port 8080

# 指定主机和端口
moyan web --host 0.0.0.0 --port 8080
```

### 输出示例

```
🌐 启动Web界面...
🔗 地址: http://localhost:8501
💡 提示: 按 Ctrl+C 停止服务

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.100:8501
```

## 🔍 使用技巧

### 1. 股票代码格式

```bash
# 支持的格式
moyan analyze 002167    # 6位数字代码
moyan analyze 000001    # 平安银行
moyan analyze 600036    # 招商银行

# 不支持的格式
moyan analyze 2167      # ❌ 不足6位
moyan analyze 002167.SZ # ❌ 包含后缀
```

### 2. 日期格式

```bash
# 正确的日期格式 (YYYYMMDD)
moyan analyze 002167 --start 20250101 --end 20250930

# 错误的日期格式
moyan analyze 002167 --start 2025-01-01  # ❌ 包含连字符
moyan analyze 002167 --start 25/01/01    # ❌ 错误格式
```

### 3. 批量分析技巧

```bash
# 使用文件存储股票列表
echo "002167,300308,601138" > stocks.txt
moyan batch $(cat stocks.txt)

# 分析特定板块
moyan batch 002167,002415,002460  # 新材料板块
moyan batch 300308,300750,300896  # 光通信板块
```

### 4. 输出管理

```bash
# 创建日期目录
mkdir analysis_$(date +%Y%m%d)
moyan analyze 002167 --output analysis_$(date +%Y%m%d)

# 批量分析到指定目录
moyan batch 002167,300308 --output ./results/$(date +%Y%m%d)
```

### 5. 组合使用

```bash
# 完整的分析命令
moyan analyze 002167 \
  --kline 15m \
  --start 20250801 \
  --end 20250928 \
  --output ./analysis/002167_15m \
  --verbose
```

## ❌ 常见错误

### 1. 股票代码错误

```bash
❌ 请输入正确的6位数字股票代码
# 解决: 确保股票代码为6位数字
```

### 2. 日期格式错误

```bash
❌ 开始日期格式错误，请使用YYYYMMDD格式
# 解决: 使用正确的日期格式，如 20250101
```

### 3. K线级别错误

```bash
❌ 不支持的K线级别: 5m
# 解决: 使用支持的级别 (15m, 30m, 1h, 1d, 1wk, 1mo)
```

### 4. 网络连接错误

```bash
❌ 数据获取失败: HTTPSConnectionPool...
# 解决: 检查网络连接，或稍后重试
```

### 5. 依赖缺失

```bash
❌ Streamlit未安装，请运行: pip install streamlit
# 解决: 安装缺失的依赖包
```

## 🆘 获取帮助

### 命令行帮助

```bash
# 查看主帮助
moyan --help

# 查看特定命令帮助
moyan analyze --help
moyan batch --help
moyan web --help
```

### 详细文档

- 📖 [快速开始](quick_start.md)
- 🔧 [安装指南](installation.md)
- 📚 [使用教程](tutorial.md)
- ❓ [常见问题](../faq.md)

---

**掌握这些CLI命令，您就能高效使用墨岩缠论分析系统了！** 🚀
