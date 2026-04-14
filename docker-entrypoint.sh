#!/bin/bash
set -e

# 入口脚本：支持本地和容器两种启动模式

# 检测是否在容器中运行
if [ -f /.dockerenv ] || [ "${CONTAINER:-}" = "true" ]; then
    CONTAINER_MODE=true
else
    CONTAINER_MODE=false
fi

if [ "$CONTAINER_MODE" = "true" ]; then
    echo "=== 文件服务器启动 [容器模式] ==="
    echo "Python版本: $(python --version)"
    echo "工作目录: $(pwd)"
    echo "服务端口: ${PORT:-8000}"
    echo "日志级别: ${LOG_LEVEL:-INFO}"

    # 确保上传目录和临时目录存在
    mkdir -p /data/uploads
    mkdir -p /app/tmp

    # 修复挂载目录的权限（必须在root下执行）
    chown -R appuser:appuser /data /app/tmp

    # 显示目录内容
    echo "服务目录内容:"
    ls -la /data/

    echo ""
    echo "切换至 appuser 启动服务器..."
    echo "========================"

    # 使用 gosu 降权执行主命令，保证文件生成权限正确
    exec gosu appuser "$@"
else
    # 本地模式：直接运行，不切换用户
    exec "$@"
fi
