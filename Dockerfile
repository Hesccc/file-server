# 使用官方 Python 镜像
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HOST=0.0.0.0 \
    LOG_LEVEL=INFO \
    CONTAINER=true

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# 创建用户和目录
RUN useradd --create-home --shell /bin/bash appuser && \
    mkdir -p /app/tmp /data/uploads && \
    chown -R appuser:appuser /app /data

WORKDIR /app

# 先复制并安装 Python 依赖（利用缓存层）
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码（按优先级分层复制以优化缓存）
COPY --chown=appuser:appuser server.py /app/
COPY --chown=appuser:appuser app/ /app/app/
COPY --chown=appuser:appuser templates/ /app/templates/
COPY --chown=appuser:appuser static/ /app/static/
COPY --chown=appuser:appuser docker-entrypoint.sh /app/

# 权限处理
RUN chmod +x /app/docker-entrypoint.sh

# 暴露端口（与 ENV PORT 保持一致）
EXPOSE 8000

# 健康检查：确保访问的是容器内的 8000 端口
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动脚本
ENTRYPOINT ["bash", "/app/docker-entrypoint.sh"]

# 默认执行命令（容器模式下无需传参，使用环境变量）
CMD ["python", "server.py"]