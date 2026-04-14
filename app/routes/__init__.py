"""
路由模块
"""
from .system import system_bp
from .static import static_bp
from .operations import operations_bp
from .upload import upload_bp
from .files import files_bp


def register_blueprints(app):
    """注册所有蓝图"""
    app.register_blueprint(system_bp)
    app.register_blueprint(static_bp)
    app.register_blueprint(operations_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(files_bp)
