"""
文件工具函数
"""
import os


def fbytes(B: float) -> str:
    """将字节数转换为人类可读的格式"""
    B = float(B)
    KB = 1024.0
    MB = KB ** 2
    GB = KB ** 3
    if B < KB:
        return '{0:.0f} Bytes'.format(B)
    elif KB <= B < MB:
        return '{0:.2f} KB'.format(B / KB)
    elif MB <= B < GB:
        return '{0:.2f} MB'.format(B / MB)
    else:
        return '{0:.2f} GB'.format(B / GB)


def get_file_icon(name: str, is_dir: bool) -> str:
    """根据文件名获取图标类名"""
    if is_dir:
        return 'icon-dir'

    ext = os.path.splitext(name)[1].lower()
    if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg']:
        return 'icon-image'
    elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
        return 'icon-archive'
    elif ext in ['.pdf']:
        return 'icon-pdf'
    elif ext in ['.doc', '.docx']:
        return 'icon-doc'
    elif ext in ['.xls', '.xlsx']:
        return 'icon-xls'
    elif ext in ['.py', '.js', '.html', '.css', '.json', '.md']:
        return 'icon-code'
    else:
        return 'icon-file'
