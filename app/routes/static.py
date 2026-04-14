"""
静态文件路由
"""
import os
from flask import send_file, Blueprint

static_bp = Blueprint('static', __name__)


def get_static_path(filename: str) -> str:
    """获取静态文件路径"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, 'static', filename)


@static_bp.route('/static/css/style.css')
def serve_css():
    """提供 CSS 文件"""
    css_path = get_static_path('css/style.css')
    if os.path.exists(css_path):
        return send_file(css_path, mimetype='text/css')
    return "CSS not found", 404


@static_bp.route('/static/js/script.js')
def serve_js():
    """提供 JS 文件"""
    js_path = get_static_path('js/script.js')
    if os.path.exists(js_path):
        return send_file(js_path, mimetype='application/javascript')
    return "JS not found", 404
