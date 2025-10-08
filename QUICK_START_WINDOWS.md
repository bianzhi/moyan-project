# 墨岩缠论分析系统 - Windows 快速安装指南

## 🎯 5分钟快速开始

### 📋 您需要的文件
- `moyan-czsc-docker.tar` (Docker镜像文件，1.2GB)
- `docker-compose.yml` 或 `docker-compose-windows.yml` (配置文件)
- `start-windows.bat` (Windows启动脚本)
- `WINDOWS_USER_GUIDE.md` (详细用户指南)

### 🚀 快速安装步骤

#### 第1步：安装Docker Desktop (首次使用)
```
1. 访问：https://www.docker.com/products/docker-desktop/
2. 下载并安装 Docker Desktop for Windows
3. 重启电脑
4. 启动 Docker Desktop，等待绿色状态
```

#### 第2步：准备文件
```
1. 创建文件夹：C:\moyan-czsc
2. 将所有文件复制到该文件夹
3. 确保文件完整：
   ✅ moyan-czsc-docker.tar (1.2GB)
   ✅ docker-compose.yml
   ✅ start-windows.bat
```

#### 第3步：一键启动
```
1. 双击 start-windows.bat
2. 等待自动导入镜像和启动服务
3. 浏览器自动打开 http://localhost:8501
4. 开始使用！
```

## 🎮 使用方法

### 基本操作
1. **输入股票代码**: 在左侧输入框输入（如：000001、600036、300363）
2. **选择参数**: K线级别、时间范围等
3. **开始分析**: 点击分析按钮
4. **查看结果**: 查看缠论分析图表和统计信息

### 功能特色
- ✅ 完整缠论分析（分型、笔、线段、中枢、背驰）
- ✅ 多时间级别（日线、小时线、分钟线）
- ✅ 交互式图表（鼠标悬停查看详情）
- ✅ 自动数据获取（支持A股所有股票）
- ✅ 智能买卖点识别

## 🛠️ 常用操作

### 服务管理
```cmd
# 启动服务
双击 start-windows.bat

# 停止服务
docker-compose down

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 数据查看
```
分析图表：output\charts\
分析报告：output\reports\
系统日志：logs\
```

## ❓ 常见问题

**Q: Docker Desktop启动失败？**
A: 确保启用了WSL 2功能，在"启用或关闭Windows功能"中勾选相关选项后重启。

**Q: 端口8501被占用？**
A: 运行 `netstat -ano | findstr :8501` 查看占用进程，使用任务管理器结束该进程。

**Q: 镜像导入失败？**
A: 确保有足够磁盘空间(5GB+)，以管理员身份运行脚本。

**Q: 无法访问localhost:8501？**
A: 检查防火墙设置，尝试访问 http://127.0.0.1:8501

## 📞 技术支持

- **系统要求**: Windows 10/11 (64位) + 4GB内存
- **推荐配置**: 8GB内存 + 10GB磁盘空间
- **网络要求**: 首次运行需要网络获取股票数据

---

🎊 **开始您的缠论分析之旅！** 🎊
