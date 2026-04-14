"""
系统路由：健康检查、版本信息
"""
import sys
from datetime import datetime, timezone
from flask import jsonify, Blueprint, current_app

from ..config import __version__

system_bp = Blueprint('system', __name__)


@system_bp.route('/health')
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": __version__
    })


@system_bp.route('/version')
def version():
    """版本信息端点"""
    return jsonify({
        "version": __version__,
        "python": sys.version,
        "server": f"SimpleHTTPWithUpload/{__version__} (Flask)"
    })
