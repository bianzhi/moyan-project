# Docker镜像分发指南

## 🚫 为什么不上传到Git

Docker镜像文件 `moyan-czsc-docker.tar` (1.2GB) 太大，不适合上传到Git仓库：

- ✅ Git仓库应该保持轻量级
- ✅ 避免克隆仓库时下载大文件
- ✅ 节省Git存储空间和带宽
- ✅ 提高仓库克隆和拉取速度

## 📦 Docker镜像分发方式

### 方式1：云存储分享
```
推荐平台：
• 百度网盘 / 阿里云盘 / 腾讯微云
• Google Drive / OneDrive / Dropbox
• 对象存储服务 (OSS/S3/COS)

分享内容：
• moyan-czsc-docker.tar (1.2GB)
• 配套的Windows用户指南
```

### 方式2：Docker Hub发布
```bash
# 1. 标记镜像
docker tag moyan-project-moyan-czsc:latest username/moyan-czsc:latest

# 2. 推送到Docker Hub
docker push username/moyan-czsc:latest

# 3. 用户拉取
docker pull username/moyan-czsc:latest
```

### 方式3：私有Registry
```bash
# 使用企业私有镜像仓库
docker tag moyan-project-moyan-czsc:latest registry.company.com/moyan-czsc:latest
docker push registry.company.com/moyan-czsc:latest
```

### 方式4：本地传输
```
• U盘/移动硬盘拷贝
• 局域网文件共享
• FTP/SFTP服务器
```

## 🛠️ 用户获取Docker镜像的方法

### 方法1：从分享链接下载
```bash
# 1. 下载 moyan-czsc-docker.tar 到本地
# 2. 导入Docker镜像
docker load -i moyan-czsc-docker.tar

# 3. 验证导入
docker images | grep moyan
```

### 方法2：从Docker Hub拉取
```bash
# 直接拉取（如果已发布）
docker pull username/moyan-czsc:latest

# 重新标记为本地名称（可选）
docker tag username/moyan-czsc:latest moyan-project-moyan-czsc:latest
```

### 方法3：本地构建
```bash
# 从源码构建（需要网络）
git clone <repository>
cd moyan-project
docker-compose build
```

## 📋 Git仓库包含的Docker文件

```
✅ 包含在Git中：
├── Dockerfile                    # 镜像构建配置
├── docker-compose.yml           # 容器编排配置
├── docker-compose-windows.yml   # Windows专用配置
├── requirements-docker.txt      # Docker专用依赖
├── start.sh                     # Linux/macOS启动脚本
├── start-windows.bat            # Windows启动脚本
├── .dockerignore               # Docker构建忽略文件
└── README_DOCKER.md            # Docker使用文档

❌ 不包含在Git中：
├── moyan-czsc-docker.tar       # Docker镜像文件 (1.2GB)
├── docker-logs/                # 容器运行日志
└── docker-volumes/             # Docker卷数据
```

## 🎯 推荐的分发流程

### 对于开发者：
1. **构建镜像**: `docker-compose build`
2. **导出镜像**: `docker save -o moyan-czsc-docker.tar moyan-project-moyan-czsc:latest`
3. **上传到云盘**: 将tar文件上传到云存储
4. **分享链接**: 提供下载链接给用户
5. **提供文档**: 包含完整的使用指南

### 对于用户：
1. **克隆仓库**: `git clone <repository>` (获取配置文件)
2. **下载镜像**: 从分享链接下载tar文件
3. **导入镜像**: `docker load -i moyan-czsc-docker.tar`
4. **启动服务**: `docker-compose up -d`
5. **开始使用**: 访问 http://localhost:8501

## 💡 最佳实践

### 版本管理
```
• 镜像命名: moyan-czsc-v1.0.tar
• 版本标签: moyan-project-moyan-czsc:v1.0
• 发布说明: 包含版本更新内容
```

### 文件组织
```
分享包结构：
moyan-czsc-release-v1.0/
├── moyan-czsc-docker.tar        # Docker镜像
├── docker-compose.yml          # 配置文件
├── start-windows.bat           # 启动脚本
├── WINDOWS_USER_GUIDE.md       # 用户指南
└── README_WINDOWS_PACKAGE.md   # 分享包说明
```

### 安全考虑
```
• 定期更新镜像，修复安全漏洞
• 使用官方基础镜像
• 扫描镜像漏洞
• 限制容器权限
```

## 🔄 更新流程

### 镜像更新时：
1. 修改源码并测试
2. 重新构建镜像
3. 导出新版本镜像
4. 更新分享链接
5. 通知用户更新

### 用户更新时：
1. 停止现有容器: `docker-compose down`
2. 删除旧镜像: `docker rmi moyan-project-moyan-czsc:latest`
3. 下载新镜像文件
4. 导入新镜像: `docker load -i moyan-czsc-v1.1.tar`
5. 启动新容器: `docker-compose up -d`

---

🎯 **通过合理的分发策略，既保持了Git仓库的轻量级，又确保用户能够方便地获取和使用Docker镜像！**
