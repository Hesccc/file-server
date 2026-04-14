"""
文件上传路由
"""
import os
import shutil
import time
import html
import logging
from flask import request, jsonify, Blueprint
from werkzeug.utils import secure_filename
from typing import Optional, List

from ..config import get_serve_dir
from ..utils.template import render_simple_template

upload_bp = Blueprint('upload', __name__)
logger = logging.getLogger('SimpleHTTPServer')


def handle_upload_response(success: bool, message: str, uploaded_paths: Optional[List[str]] = None):
    """处理上传响应"""
    # 检查是否需要JSON响应
    accept_header = request.headers.get('Accept', '')
    if 'application/json' in accept_header:
        return jsonify({
            "success": success,
            "message": message,
            "uploaded_paths": uploaded_paths if uploaded_paths else []
        })

    # HTML 响应
    referer = request.headers.get('Referer', '/')
    html_content = render_simple_template(
        'upload_result.html',
        alert_class='alert-success' if success else 'alert-error',
        icon='✓' if success else '✗',
        title='成功！' if success else '失败！',
        message=html.escape(message),
        back_url=html.escape(referer)
    )
    return html_content


@upload_bp.route('/', methods=['POST'])
def upload_file():
    """处理文件上传"""
    serve_dir = get_serve_dir()

    if 'file' not in request.files:
        return handle_upload_response(False, "没有找到文件")

    files = request.files.getlist('file')
    uploaded_files = []
    uploaded_paths = []

    for file in files:
        if file.filename == '':
            continue

        # 安全处理文件名
        filename = secure_filename(file.filename)
        if not filename:
            continue

        # 构建完整的目标路径
        dest_path = os.path.join(serve_dir, filename)

        # 使用临时文件
        main_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        tmp_dir = os.path.join(main_dir, 'tmp')
        os.makedirs(tmp_dir, exist_ok=True)
        temp_fn = os.path.join(tmp_dir, f"upload_tmp_{int(time.time()*1000)}_{filename}")

        try:
            file.save(temp_fn)
            shutil.move(temp_fn, dest_path)
            uploaded_files.append(filename)
            uploaded_paths.append(dest_path)
            logger.info(f"File uploaded: {filename}")
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            if os.path.exists(temp_fn):
                try:
                    os.remove(temp_fn)
                except:
                    pass
            return handle_upload_response(False, f"上传失败: {str(e)}")

    if not uploaded_files:
        return handle_upload_response(False, "没有上传任何文件")

    return handle_upload_response(True, f"成功上传 {len(uploaded_files)} 个文件", uploaded_paths)
