# 墨岩缠论分析系统 - Windows 用户指南

## 🎯 简介

这是一个完整的缠论技术分析系统，已经打包成Docker镜像，可以在Windows环境下一键部署和运行。

## 📋 系统要求

### 硬件要求
- **内存**: 至少 4GB RAM（推荐 8GB+）
- **硬盘**: 至少 5GB 可用空间
- **处理器**: Intel/AMD 64位处理器

### 软件要求
- **操作系统**: Windows 10/11 (64位)
- **Docker Desktop**: 最新版本

## 🚀 安装步骤

### 第一步：安装 Docker Desktop

1. **下载 Docker Desktop**
   - 访问官网：https://www.docker.com/products/docker-desktop/
   - 点击 "Download for Windows"
   - 下载完成后，双击安装包进行安装

2. **安装配置**
   ```
   ✅ 选择 "Use WSL 2 instead of Hyper-V" (推荐)
   ✅ 选择 "Add shortcut to desktop"
   ✅ 完成安装后重启电脑
   ```

3. **启动验证**
   - 启动 Docker Desktop
   - 等待 Docker 引擎启动完成（状态栏显示绿色）
   - 打开 CMD 或 PowerShell，运行：
   ```cmd
   docker --version
   ```
   - 应该显示类似：`Docker version 24.0.x, build xxx`

### 第二步：准备文件

1. **创建工作目录**
   ```cmd
   mkdir C:\moyan-czsc
   cd C:\moyan-czsc
   ```

2. **复制必要文件**
   将以下文件复制到 `C:\moyan-czsc` 目录：
   - `moyan-czsc-docker.tar` (Docker镜像文件)
   - `docker-compose.yml` (容器编排文件)

### 第三步：导入和运行

1. **导入 Docker 镜像**
   ```cmd
   cd C:\moyan-czsc
   docker load -i moyan-czsc-docker.tar
   ```
   
   等待导入完成，应该看到：
   ```
   Loaded image: moyan-project-moyan-czsc:latest
   ```

2. **启动服务**
   ```cmd
   docker-compose up -d
   ```
   
   成功启动后应该看到：
   ```
   Container moyan-czsc-app  Started
   ```

3. **访问应用**
   - 打开浏览器
   - 访问：http://localhost:8501
   - 开始使用缠论分析系统！

## 🎮 使用指南

### 基本操作

1. **输入股票代码**
   - 在左侧输入框输入股票代码（如：000001、600036）
   - 支持A股所有股票

2. **选择分析参数**
   - **K线级别**: 1d(日线)、1h(小时)、30m、15m等
   - **时间范围**: 选择分析的时间窗口
   - **显示选项**: 勾选需要显示的技术指标

3. **查看分析结果**
   - **主图**: K线图 + 均线 + 缠论标记
   - **副图**: 成交量、MACD、RSI等指标
   - **统计面板**: 买卖点、背驰、中枢等统计信息

### 功能特色

- ✅ **完整缠论分析**: 分型、笔、线段、中枢、背驰
- ✅ **多级别分析**: 支持日线到分钟级别
- ✅ **交互式图表**: 鼠标悬停查看详细信息
- ✅ **实时数据**: 自动获取最新股票数据
- ✅ **智能标记**: 自动识别买卖点和技术形态

## 🛠️ 常用命令

### 服务管理
```cmd
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看服务状态
docker-compose ps
```

### 日志查看
```cmd
# 查看实时日志
docker-compose logs -f

# 查看最近100行日志
docker-compose logs --tail=100
```

### 数据管理
```cmd
# 查看分析结果
dir output\charts     # 图表文件
dir output\reports    # 分析报告

# 查看系统日志
dir logs
```

## 🔧 故障排除

### 常见问题

**1. Docker Desktop 启动失败**
```
解决方案：
1. 确保已启用 WSL 2 功能
2. 在 "控制面板 > 程序 > 启用或关闭Windows功能" 中启用：
   - Hyper-V (如果支持)
   - 适用于Linux的Windows子系统
   - 虚拟机平台
3. 重启电脑
```

**2. 端口 8501 被占用**
```cmd
# 查看端口占用
netstat -ano | findstr :8501

# 终止占用进程 (PID为查询到的进程ID)
taskkill /PID <PID> /F
```

**3. 镜像导入失败**
```
解决方案：
1. 确保 moyan-czsc-docker.tar 文件完整
2. 确保有足够的磁盘空间 (至少5GB)
3. 以管理员身份运行 CMD/PowerShell
```

**4. 无法访问 localhost:8501**
```
检查步骤：
1. 确认容器正在运行：docker-compose ps
2. 检查防火墙设置
3. 尝试访问：http://127.0.0.1:8501
4. 重启Docker服务
```

### 性能优化

**1. 内存设置**
- 打开 Docker Desktop
- Settings > Resources > Memory
- 建议设置为 4GB 或更多

**2. 磁盘清理**
```cmd
# 清理未使用的镜像和容器
docker system prune -a

# 清理Docker缓存
docker builder prune -a
```

## 📁 目录结构

```
C:\moyan-czsc\
├── moyan-czsc-docker.tar    # Docker镜像文件
├── docker-compose.yml       # 容器编排配置
├── output\                  # 分析结果输出
│   ├── charts\             # 图表文件 (.png)
│   └── reports\            # 分析报告 (.md)
└── logs\                   # 系统日志
```

## 🎯 快速启动脚本

创建 `start.bat` 文件，内容如下：

```batch
@echo off
echo 🚀 启动墨岩缠论分析系统...
echo.

REM 检查Docker是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker未运行，请启动Docker Desktop
    pause
    exit /b 1
)

REM 启动服务
echo 📦 启动容器服务...
docker-compose up -d

if %errorlevel% equ 0 (
    echo.
    echo ✅ 服务启动成功！
    echo 📊 访问地址: http://localhost:8501
    echo.
    echo 💡 常用命令:
    echo   停止服务: docker-compose down
    echo   查看日志: docker-compose logs -f
    echo   查看状态: docker-compose ps
    echo.
    pause
) else (
    echo ❌ 服务启动失败，请检查错误信息
    pause
)
```

双击 `start.bat` 即可一键启动！

## 🎉 开始使用

1. **运行启动脚本**: 双击 `start.bat`
2. **打开浏览器**: 访问 http://localhost:8501
3. **输入股票代码**: 开始您的缠论分析之旅！

## 📞 支持信息

- **项目名称**: 墨岩缠论分析系统
- **技术支持**: 如遇问题，请检查本指南的故障排除部分
- **系统要求**: Windows 10/11 + Docker Desktop
- **推荐配置**: 8GB内存 + 10GB磁盘空间

---

🎊 **祝您使用愉快！通过缠论分析，洞察市场趋势！** 🎊
