"""
Flask 应用初始化
"""
from flask import Flask
from .routes import register_blueprints


def create_app():
    """创建 Flask 应用实例"""
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = None  # 不限制上传大小

    # 注册蓝图
    register_blueprints(app)

    return app
