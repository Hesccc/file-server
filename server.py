#!/usr/bin/env python3
"""
Simple HTTP File Server With Upload - Flask Edition

支持优雅退出的文件服务器，适用于容器化部署。
"""

import os
import signal
import logging
import threading
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('SimpleHTTPServer')

from app import create_app
from app.config import __version__, get_config, set_serve_dir

# 全局状态
_shutting_down = False
_shutdown_event = threading.Event()


def print_banner(config):
    """打印启动横幅"""
    host_display = config['host'] or '0.0.0.0 (所有接口)'
    dev_mode = "[开发模式]" if config.get('dev') else ""
    container_mode = "[容器模式]" if config.get('container_mode') else "[本地模式]"

    banner = f"""
===============================================================
          Simple HTTP Server with Upload v{__version__}
                    (Flask Edition)
===============================================================
  绑定地址: {host_display}
  端口:     {config['port']}
  服务目录: {config['directory']}
  日志级别: {config['log_level']}
  运行模式: {container_mode} {dev_mode}
===============================================================
  健康检查: http://{config['host'] or 'localhost'}:{config['port']}/health
  版本信息: http://{config['host'] or 'localhost'}:{config['port']}/version
===============================================================
    """
    print(banner)


def setup_signal_handlers():
    """设置信号处理器"""
    def handler(signum, _):
        global _shutting_down
        if _shutting_down:
            signal.signal(signum, signal.SIG_DFL)
            os.kill(os.getpid(), signum)
            return
        _shutting_down = True

        signal_name = {signal.SIGTERM: 'SIGTERM', signal.SIGINT: 'SIGINT'}
        if hasattr(signal, 'SIGQUIT'):
            signal_name[signal.SIGQUIT] = 'SIGQUIT'
        sig_name = signal_name.get(signum, str(signum))

        logger.info(f"接收到 {sig_name} 信号，开始优雅关闭...")

        # 恢复默认信号处理
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        if hasattr(signal, 'SIGQUIT'):
            signal.signal(signal.SIGQUIT, signal.SIG_DFL)

        # 设置关闭事件，通知主线程退出
        _shutdown_event.set()

    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)
    if hasattr(signal, 'SIGQUIT'):
        signal.signal(signal.SIGQUIT, handler)


def run_server(app, config):
    """运行服务器（支持优雅关闭）"""
    host = config['host'] or '0.0.0.0'
    port = config['port']

    logger.info(f"服务已启动: http://{host}:{port}/")
    logger.info("按 Ctrl+C 停止服务器")

    # 在单独的线程中运行服务器
    from werkzeug.serving import make_server

    try:
        server = make_server(
            host, port, app,
            threaded=True,
            processes=1
        )
    except Exception as e:
        logger.error(f"启动服务器失败: {e}")
        sys.exit(1)

    # 启动服务器线程
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # 等待关闭信号
    _shutdown_event.wait()

    logger.info("正在关闭服务器...")
    server.shutdown()
    logger.info("服务器已关闭")


def main():
    """主入口函数"""
    global _shutting_down
    _shutting_down = False

    config = get_config()

    # 设置服务目录
    set_serve_dir(config['directory'])

    logging.getLogger().setLevel(getattr(logging, config['log_level']))

    print_banner(config)

    # 创建 Flask 应用
    app = create_app()

    # 开发模式：启用自动重载，禁用信号处理器（由 Flask 处理）
    if config['dev']:
        logger.info("[开发模式] 已启用 - 代码修改将自动重载")
        app.run(
            host=config['host'] or '0.0.0.0',
            port=config['port'],
            threaded=True,
            use_reloader=True,
            debug=True
        )
    else:
        setup_signal_handlers()
        run_server(app, config)


if __name__ == '__main__':
    main()
