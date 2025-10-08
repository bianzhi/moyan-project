# 墨岩缠论分析系统 - 简化Docker部署

## 🚀 方案一：本地Python环境（推荐）

如果您已经有Python环境，推荐直接使用：

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m streamlit run src/moyan/web/app.py --server.port 8501 --server.address 0.0.0.0
```

## 🐳 方案二：Docker部署

### 快速启动脚本

我们提供了以下Docker配置文件：

1. **Dockerfile** - Docker镜像构建文件
2. **docker-compose.yml** - Docker Compose配置
3. **start.sh** (Linux/macOS) - 自动化启动脚本
4. **start.bat** (Windows) - Windows启动脚本

### 使用步骤

1. **确保Docker已安装并运行**
   ```bash
   docker --version
   docker-compose --version
   ```

2. **运行启动脚本**
   ```bash
   # Linux/macOS
   ./start.sh
   
   # Windows
   start.bat
   ```

3. **手动启动（如果脚本失败）**
   ```bash
   # 构建镜像
   docker-compose build
   
   # 启动服务
   docker-compose up -d
   ```

### 网络问题解决方案

如果遇到Docker Hub访问问题，可以：

1. **使用国内镜像源**
   ```bash
   # 编辑Docker配置
   sudo nano /etc/docker/daemon.json
   
   # 添加以下内容
   {
     "registry-mirrors": [
       "https://docker.mirrors.ustc.edu.cn",
       "https://hub-mirror.c.163.com",
       "https://mirror.baidubce.com"
     ]
   }
   
   # 重启Docker
   sudo systemctl restart docker
   ```

2. **使用本地Python环境**（推荐）
   直接使用方案一，无需Docker

## 📁 项目结构

```
moyan-project/
├── src/moyan/              # 源代码
├── requirements.txt        # Python依赖
├── Dockerfile             # Docker镜像构建
├── docker-compose.yml     # Docker编排
├── start.sh               # Linux启动脚本
├── start.bat              # Windows启动脚本
└── README_DOCKER.md       # 详细文档
```

## 🔧 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```

## 📞 技术支持

如果遇到问题：
1. 优先使用本地Python环境（方案一）
2. 检查Docker和网络连接
3. 查看详细错误日志

---

🎉 **选择最适合您的部署方案！**
