# 墨岩缠论分析系统 Docker 部署指南

## 📦 Docker镜像获取

> **注意**: Docker镜像文件 (1.2GB) 不包含在Git仓库中，需要单独获取。

### 🎯 获取方式

#### 方式1：从构建好的镜像文件
1. **获取镜像文件**: 从分享链接下载 `moyan-czsc-docker.tar`
2. **导入镜像**: `docker load -i moyan-czsc-docker.tar`
3. **启动服务**: `docker-compose up -d`

#### 方式2：从源码构建（需要网络）
1. **克隆仓库**: `git clone <repository>`
2. **构建镜像**: `docker-compose build`
3. **启动服务**: `docker-compose up -d`

## 🚀 快速开始

### 方法一：使用启动脚本（推荐）

**Linux/macOS:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

### 方法二：手动启动

1. **构建并启动服务**
```bash
docker-compose up -d --build
```

2. **访问应用**
打开浏览器访问：http://localhost:8501

## 📋 系统要求

- Docker Engine 20.0+
- Docker Compose 2.0+
- 至少 2GB 可用内存
- 至少 1GB 可用磁盘空间

## 🛠️ 常用命令

### 服务管理
```bash
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
```bash
# 查看实时日志
docker-compose logs -f

# 查看指定服务日志
docker-compose logs moyan-czsc

# 查看最近100行日志
docker-compose logs --tail=100
```

### 镜像管理
```bash
# 重新构建镜像
docker-compose build --no-cache

# 拉取最新镜像
docker-compose pull

# 查看镜像
docker images | grep moyan
```

## 📁 目录结构

```
moyan-project/
├── Dockerfile              # Docker镜像构建文件
├── docker-compose.yml      # Docker Compose配置
├── .dockerignore           # Docker忽略文件
├── start.sh                # Linux/macOS启动脚本
├── start.bat               # Windows启动脚本
├── output/                 # 分析结果输出目录（持久化）
│   ├── charts/            # 图表文件
│   └── reports/           # 分析报告
└── logs/                  # 日志文件目录（持久化）
```

## ⚙️ 配置说明

### 环境变量
可以通过修改 `docker-compose.yml` 中的环境变量来配置系统：

```yaml
environment:
  - PYTHONPATH=/app
  - PYTHONUNBUFFERED=1
  - STREAMLIT_SERVER_PORT=8501
  - STREAMLIT_SERVER_ADDRESS=0.0.0.0
  - STREAMLIT_SERVER_HEADLESS=true
  - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

### 端口配置
默认端口为8501，如需修改请编辑 `docker-compose.yml`：

```yaml
ports:
  - "8501:8501"  # 改为 "自定义端口:8501"
```

### 数据持久化
系统自动将以下目录挂载到宿主机：
- `./output` - 分析结果和图表
- `./logs` - 应用日志

## 🔧 故障排除

### 1. 端口被占用
```bash
# 查看端口占用
lsof -i :8501

# 或使用其他端口
# 修改 docker-compose.yml 中的端口映射
```

### 2. 内存不足
```bash
# 查看容器资源使用
docker stats moyan-czsc-app

# 增加Docker内存限制（在docker-compose.yml中）
deploy:
  resources:
    limits:
      memory: 4G
```

### 3. 服务启动失败
```bash
# 查看详细日志
docker-compose logs moyan-czsc

# 检查容器状态
docker-compose ps

# 重新构建镜像
docker-compose build --no-cache
```

### 4. 数据源连接问题
如果遇到网络连接问题，可以：
1. 检查网络连接
2. 尝试重启容器
3. 查看应用日志了解具体错误

## 🌟 功能特性

### 默认启用的功能
- ✅ K线图
- ✅ 成交量
- ✅ 移动平均线（MA5 + MA10）
- ✅ 上升笔 / 下降笔
- ✅ 线段
- ✅ 中枢
- ✅ MACD指标
- ✅ 背驰标记

### 可选功能
- 分型标记（顶分型/底分型）
- 买卖点标记（三类买卖点）
- RSI指标
- 布林带指标

### 数据源优化
- 🚀 Sina数据源：支持分钟级别数据，最多1500条
- 🛡️ Akshare数据源：稳定的日线/周线/月线数据
- 🔄 智能数据源选择：根据K线级别自动选择最优数据源
- 📊 数据完整性检查：自动验证和清理数据

## 📞 技术支持

如果遇到问题，请：
1. 查看日志文件：`docker-compose logs -f`
2. 检查系统资源：`docker stats`
3. 确认网络连接正常
4. 重启服务：`docker-compose restart`

## 🔄 更新系统

```bash
# 停止服务
docker-compose down

# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

---

🎉 **享受使用墨岩缠论分析系统！**
