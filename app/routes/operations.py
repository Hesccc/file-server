"""
文件操作路由：删除、重命名、移动
"""
import os
import shutil
import logging
from flask import jsonify, request, Blueprint
from werkzeug.utils import secure_filename

from ..config import get_serve_dir

operations_bp = Blueprint('operations', __name__)
logger = logging.getLogger('SimpleHTTPServer')


@operations_bp.route('/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    """处理文件删除"""
    serve_dir = get_serve_dir()
    file_path = os.path.join(serve_dir, secure_filename(filename))

    # 安全检查：确保只删除当前目录下的文件
    current_dir = os.path.abspath(serve_dir)
    if not os.path.abspath(file_path).startswith(current_dir):
        return jsonify({"success": False, "message": "无法删除该路径下的文件"})

    if not os.path.exists(file_path):
        return jsonify({"success": False, "message": "文件不存在"})

    if os.path.isdir(file_path):
        return jsonify({"success": False, "message": "无法删除目录"})

    try:
        os.remove(file_path)
        logger.info(f"File deleted: {filename}")
        return jsonify({"success": True, "message": f"文件 {filename} 已删除"})
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return jsonify({"success": False, "message": f"删除失败: {str(e)}"})


@operations_bp.route('/api/rename', methods=['POST'])
def rename_file():
    """处理文件重命名"""
    serve_dir = get_serve_dir()
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "请求数据无效"})

    old_name = data.get('old_name', '').strip()
    new_name = data.get('new_name', '').strip()

    if not old_name or not new_name:
        return jsonify({"success": False, "message": "文件名不能为空"})

    # 安全检查
    old_name = secure_filename(old_name)
    new_name = secure_filename(new_name)

    if not old_name or not new_name:
        return jsonify({"success": False, "message": "文件名无效"})

    # 如果新旧名称相同（忽略大小写），视为成功
    if old_name.lower() == new_name.lower():
        return jsonify({"success": True, "message": f"文件名为 {new_name}"})

    old_path = os.path.join(serve_dir, old_name)
    new_path = os.path.join(serve_dir, new_name)

    current_dir = os.path.abspath(serve_dir)
    if not os.path.abspath(old_path).startswith(current_dir):
        return jsonify({"success": False, "message": "无法访问该路径"})
    if not os.path.abspath(new_path).startswith(current_dir):
        return jsonify({"success": False, "message": "无法访问目标路径"})

    if not os.path.exists(old_path):
        return jsonify({"success": False, "message": "源文件不存在"})

    if os.path.exists(new_path):
        return jsonify({"success": False, "message": f"文件 '{new_name}' 已存在"})

    if os.path.isdir(old_path):
        return jsonify({"success": False, "message": "无法重命名目录"})

    try:
        os.rename(old_path, new_path)
        logger.info(f"File renamed: {old_name} -> {new_name}")
        return jsonify({"success": True, "message": f"文件已重命名为 {new_name}"})
    except Exception as e:
        logger.error(f"Error renaming file: {e}")
        return jsonify({"success": False, "message": f"重命名失败: {str(e)}"})


@operations_bp.route('/api/move', methods=['POST'])
def move_file():
    """处理文件移动"""
    serve_dir = get_serve_dir()
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "请求数据无效"})

    filename = data.get('filename', '').strip()
    target_dir = data.get('target_dir', '').strip()

    if not filename:
        return jsonify({"success": False, "message": "文件名不能为空"})

    filename = secure_filename(filename)
    if not filename:
        return jsonify({"success": False, "message": "文件名无效"})

    # 源文件路径
    src_path = os.path.join(serve_dir, filename)

    # 目标目录路径
    if target_dir.startswith('/'):
        target_dir = target_dir[1:]
    target_path = os.path.join(serve_dir, target_dir, filename)

    # 安全检查
    current_dir = os.path.abspath(serve_dir)
    if not os.path.abspath(src_path).startswith(current_dir):
        return jsonify({"success": False, "message": "无法访问源文件"})
    if not os.path.abspath(target_path).startswith(current_dir):
        return jsonify({"success": False, "message": "无法访问目标目录"})

    if not os.path.exists(src_path):
        return jsonify({"success": False, "message": "源文件不存在"})

    if os.path.isdir(src_path):
        return jsonify({"success": False, "message": "无法移动目录"})

    # 确保目标目录存在
    target_dir_path = os.path.dirname(target_path)
    if not os.path.exists(target_dir_path):
        try:
            os.makedirs(target_dir_path, exist_ok=True)
        except Exception as e:
            return jsonify({"success": False, "message": f"创建目标目录失败: {str(e)}"})

    if os.path.exists(target_path):
        return jsonify({"success": False, "message": "目标位置已存在同名文件"})

    try:
        shutil.move(src_path, target_path)
        logger.info(f"File moved: {filename} -> {target_dir}/")
        return jsonify({"success": True, "message": f"文件已移动到 {target_dir}/"})
    except Exception as e:
        logger.error(f"Error moving file: {e}")
        return jsonify({"success": False, "message": f"移动失败: {str(e)}"})


@operations_bp.route('/api/directories', methods=['GET'])
def get_directories():
    """获取所有目录列表（用于移动文件时选择目标目录）"""
    serve_dir = get_serve_dir()

    def list_dirs(base_path, rel_path=''):
        dirs = []
        full_path = os.path.join(base_path, rel_path)
        if not os.path.exists(full_path):
            return dirs

        for item in os.listdir(full_path):
            item_rel = os.path.join(rel_path, item) if rel_path else item
            item_full = os.path.join(full_path, item)
            if os.path.isdir(item_full):
                dirs.append(item_rel)
                dirs.extend(list_dirs(base_path, item_rel))
        return dirs

    try:
        directories = list_dirs(serve_dir)
        return jsonify({"success": True, "directories": directories})
    except Exception as e:
        logger.error(f"Error listing directories: {e}")
        return jsonify({"success": False, "message": str(e)})
