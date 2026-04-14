"""
Flask 应用配置
"""
import os
from typing import Dict, Any

__version__ = "3.0.0"

# 全局状态
SERVE_DIRECTORY: str = os.getcwd()
_template_cache: Dict[str, str] = {}


def load_dotenv():
    """加载 .env 文件中的环境变量（如果存在）"""
    try:
        from dotenv import load_dotenv as _load_dotenv
        # 尝试从当前工作目录加载 .env 文件
        env_path = os.path.join(os.getcwd(), '.env')
        if os.path.exists(env_path):
            _load_dotenv(env_path)
    except ImportError:
        # python-dotenv 未安装，跳过
        pass


def get_config() -> Dict[str, Any]:
    """获取配置（支持本地和容器两种启动模式）"""
    import argparse

    # 检测是否在容器环境中运行
    in_container = os.path.exists('/.dockerenv') or os.environ.get('CONTAINER', '').lower() in ('true', '1')

    # 本地模式：加载 .env 文件（如果存在）
    if not in_container:
        load_dotenv()

    # 默认目录：容器模式使用 /data，本地模式使用当前目录
    default_directory = '/data' if in_container else os.getcwd()

    config = {
        'host': '',
        'port': 8000,
        'directory': default_directory,
        'log_level': 'INFO',
        'dev': False,
        'container_mode': in_container
    }

    # 从环境变量读取配置（.env 文件已加载到环境变量中）
    if 'HOST' in os.environ:
        config['host'] = os.environ['HOST']
    if 'PORT' in os.environ:
        config['port'] = int(os.environ['PORT'])
    if 'SERVE_DIRECTORY' in os.environ:
        config['directory'] = os.environ['SERVE_DIRECTORY']
    if 'LOG_LEVEL' in os.environ:
        config['log_level'] = os.environ['LOG_LEVEL']
    if 'FLASK_DEV' in os.environ:
        config['dev'] = os.environ['FLASK_DEV'].lower() in ('true', '1', 'yes', 'on')

    parser = argparse.ArgumentParser(description='Simple HTTP Server with Upload (Flask)')
    parser.add_argument('--bind', '-b', default=config['host'], metavar='ADDRESS',
                        help='Specify bind address [default: all interfaces]')
    parser.add_argument('port', action='store', nargs='?', type=int,
                        default=config['port'], help=f'Specify port [default: {config["port"]}]')
    parser.add_argument('--directory', '-d', default=config['directory'],
                        help='Directory to serve [default: current directory]')
    parser.add_argument('--log-level', default=config['log_level'],
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level')
    parser.add_argument('--dev', action='store_true',
                        help='Enable development mode (auto-reload on code changes)')

    # 容器模式：允许无参数运行（使用环境变量或默认值）
    # 本地模式：无参数时打印帮助
    args = parser.parse_args()
    config['host'] = args.bind
    config['port'] = args.port
    config['directory'] = args.directory
    config['log_level'] = args.log_level
    config['dev'] = args.dev

    return config


def get_serve_dir() -> str:
    """获取服务目录"""
    return SERVE_DIRECTORY


def set_serve_dir(directory: str):
    """设置服务目录"""
    global SERVE_DIRECTORY
    SERVE_DIRECTORY = directory
