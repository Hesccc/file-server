"""
文件浏览和下载路由
"""
import os
import html
import mimetypes
import time
import logging
from flask import send_file, redirect, request, Blueprint

from ..config import get_serve_dir
from ..utils.template import render_simple_template
from ..utils.file import fbytes, get_file_icon

files_bp = Blueprint('files', __name__)
logger = logging.getLogger('SimpleHTTPServer')


@files_bp.route('/', defaults={'path': ''})
@files_bp.route('/<path:path>')
def serve_path(path):
    """处理文件浏览和下载"""
    serve_dir = get_serve_dir()

    # 获取请求路径
    if request.path.endswith('/') or request.path == '/':
        # 目录列表
        serve_dir_path = serve_dir if not path else os.path.join(serve_dir, path)
        if not os.path.isdir(serve_dir_path):
            return "Directory not found", 404
        return list_directory(serve_dir_path, request.path)
    else:
        # 文件下载
        file_path = os.path.join(serve_dir, path)
        if not os.path.exists(file_path):
            return "File not found", 404
        if os.path.isdir(file_path):
            # 重定向到带斜杠的路径
            return redirect(request.path + '/')

        # 发送文件
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        return send_file(file_path, mimetype=mime_type)


def list_directory(path: str, url_path: str):
    """生成目录列表HTML"""
    from ..config import __version__

    try:
        list_dir = os.listdir(path)
    except os.error:
        return "No permission to list directory", 404

    list_dir.sort(key=lambda a: a.lower())
    displaypath = html.escape(url_path)

    # 构建文件列表HTML
    file_rows = []
    if url_path != '/':
        file_rows.append('<tr><td colspan="4"><a href="../" class="file-link"><span class="icon-dir-open"></span>上级目录</a></td></tr>')

    for name in list_dir:
        fullname = os.path.join(path, name)
        displayname = name
        is_dir = os.path.isdir(fullname)

        fsize = fbytes(os.path.getsize(fullname)) if not is_dir else ''
        created_date = time.ctime(os.path.getctime(fullname)) if not is_dir else ''

        if is_dir:
            displayname = name + "/"
            linkname = name + "/"
        else:
            linkname = name

        icon = get_file_icon(name, is_dir)

        # 操作按钮（只对文件显示，不对目录）
        if is_dir:
            actions = ''
        else:
            actions = f'''<div class="file-actions">
                <button class="action-btn btn-rename" onclick="renameFile('{html.escape(name)}')" title="重命名">✏️</button>
                <button class="action-btn btn-move" onclick="moveFile('{html.escape(name)}')" title="移动">📦</button>
                <button class="action-btn btn-delete" onclick="deleteFile('{html.escape(name)}')" title="删除">🗑️</button>
            </div>'''

        file_rows.append(f'''<tr>
            <td><span class="{icon}"></span></td>
            <td><a href="{html.escape(linkname)}" class="file-link">{html.escape(displayname)}</a></td>
            <td class="file-size">{fsize}</td>
            <td class="file-date">{created_date}</td>
            <td class="file-actions-cell">{actions}</td>
        </tr>''')

    html_content = render_simple_template(
        'directory.html',
        displaypath=displaypath,
        file_rows="".join(file_rows),
        version=__version__
    )

    return html_content
