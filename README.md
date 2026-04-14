# Simple HTTP File Server with Upload (Flask Edition)

一个基于 Flask 的支持文件上传和优雅退出的简单HTTP文件服务器，专为容器化部署优化。

## 特性

- **基于 Flask 框架**: 使用 Flask 构建的现代Web应用，易于扩展和维护
- **现代化沉浸式 UI**: 提供带悬浮效果和移动端自适用的极简界面，文件夹统一呈现原生系统 Emoji 渲染并修复叠字干扰问题。
- **并发任务机制与图标按钮**: 左下角上传队列浮窗中支持小图标操控。彻底重写了 JavaScript 避免在刷新进度时造成 DOM 闪烁闪退等，可精准中止和删除任意并行传输的项。
- **断点截留与分离缓冲**: 为解决上传不完整导致产生碎片文件的问题，本系统将在项目根目录自动创建 `/tmp` 用于上传期间的数据切片积攒和组合，等到 `100%` 完成核对后再安全转移至目标 `upload` 文件夹。
- **优雅异常与死锁切断拦截**: 除了 `SIGTERM/SIGINT` 信号完美捕停的逻辑之外，在内核底层新增拦截并跳出由于浏览器主动强行断开导致的 `b""` （0字节）死循环等待，及完美静默拦截 `WinError 10053` 断联警告。
- **健康检查与版本**: 包含 `/health` 与 `/version` 供运维监控。

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 复制环境变量配置文件（可选）
cp .env.example .env
# 编辑 .env 文件自定义配置

# 使用默认配置（自动读取 .env 文件）
python server.py

# 指定端口和目录（命令行参数优先级高于 .env 文件）
python server.py --port 8080 --directory ./uploads --log-level DEBUG

# 绑定特定地址
python server.py --bind 127.0.0.1 --port 8080

# 开发模式（代码修改自动重载）
python server.py --dev
```

### Docker 运行

```bash
# 构建镜像
docker build -t fileserver:latest .

# 运行容器
docker run -d \
  --name fileserver \
  -p 8000:8000 \
  -v $(pwd)/uploads:/data \
  -e LOG_LEVEL=INFO \
  fileserver:latest

# 停止容器（优雅退出）
docker stop -t 30 fileserver
```

### Docker Compose 运行

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件配置参数
# PORT=8000
# LOG_LEVEL=INFO

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务（优雅退出）
docker-compose down
```

## 配置选项

### 本地模式配置（使用 .env 文件）

本地启动时会自动加载当前目录下的 `.env` 文件（如果存在）。

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件
cat .env
PORT=8080
LOG_LEVEL=DEBUG
SERVE_DIRECTORY=./uploads
HOST=127.0.0.1

# 启动服务（自动读取 .env）
python server.py
```

### 容器模式配置（使用环境变量）

容器启动时**不读取 .env 文件**，仅使用创建容器时设置的环境变量。

```bash
# 通过 docker run -e 参数设置
docker run -d \
  -p 8000:8000 \
  -e PORT=9000 \
  -e LOG_LEVEL=DEBUG \
  fileserver:latest

# 或在 docker-compose.yml 中设置
```

### 环境变量列表

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `HOST` | 绑定地址 | `0.0.0.0` |
| `PORT` | 服务端口 | `8000` |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `SERVE_DIRECTORY` | 服务目录 | `/data` (容器) 或当前目录 |
| `FLASK_DEV` | 开发模式 | `False` |

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--bind`, `-b` | 绑定地址 | 环境变量或空字符串 |
| `--port` | 服务端口 | 环境变量或8000 |
| `--directory`, `-d` | 服务目录 | 当前目录 |
| `--log-level` | 日志级别 | INFO |
| `--dev` | 开发模式（代码修改自动重载） | False |

## API 端点

### 文件服务

- `GET /` - 目录列表
- `GET /filename` - 下载文件
- `POST /` - 上传文件

### 系统端点

- `GET /health` - 健康检查
  ```json
  {
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00.000000",
    "version": "2.0.0"
  }
  ```

- `GET /version` - 版本信息
  ```json
  {
    "version": "2.0.0",
    "python": "3.11.0",
    "server": "SimpleHTTPWithUpload/2.0.0"
  }
  ```

## 优雅退出机制

服务器实现了完善的优雅退出机制，防止重复触发关闭：

### 防止重复触发

- 使用 `_shutdown_called` 标志确保关闭只执行一次
- 使用 `_shutdown_lock` 锁保护关闭状态
- 重复信号触发时恢复默认处理器并强制退出

### 信号处理

- `SIGTERM` - Docker 默认停止信号
- `SIGINT` - Ctrl+C 中断
- `SIGQUIT` - 退出信号（如果可用）

### 关闭流程

当接收到关闭信号时：

1. **检查关闭标志**: 使用锁检查 `_shutdown_called`，如果已在关闭中则处理重复信号
2. **设置关闭标志**: 标记关闭已开始
3. **恢复默认处理器**: 防止重复注册信号处理器
4. **等待活跃请求**: 最多等待5秒让活跃请求完成
5. **关闭服务器**: 最终关闭服务器

### 重复信号处理

如果在关闭过程中再次收到信号：
- 日志记录警告信息
- 恢复默认信号处理器
- 强制终止进程

## 文件结构

```text
.
├── server.py               # 主程序执行文件
├── static/                 # 样式 (style.css) 与前端引擎 (script.js)
├── templates/              # 目录索引及上传结果 HTML 模板
├── tmp/                    # 文件上传临时缓存池 (运行时自动构建)
├── Dockerfile              # Docker 构建引擎指令
├── docker-compose.yml      # Docker 组合与起停配置
├── docker-entrypoint.sh    # 容器初始化及环境起调入口
├── .dockerignore           # Docker 打包剔除规则
├── .env.example            # 容器环境变量示范文件
└── README.md               # 项目使用手册与更新纪要
```
## 效果图

![效果图](https://ovvo.oss-cn-shenzhen.aliyuncs.com/PicGo/20260414005929625.png)

## 许可证

遵循 MIT 许可证。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。
