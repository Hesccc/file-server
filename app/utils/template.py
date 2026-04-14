"""
模板处理工具
"""
import os
from typing import Dict
from ..config import _template_cache


def get_template_path(name: str) -> str:
    """获取模板文件路径"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, 'templates', name)


def load_template(name: str) -> str:
    """加载并缓存模板"""
    if name in _template_cache:
        return _template_cache[name]

    template_path = get_template_path(name)
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        _template_cache[name] = content
        return content
    except Exception as e:
        import logging
        logger = logging.getLogger('SimpleHTTPServer')
        logger.error(f"无法加载模板 {name}: {e}")
        return ""


def render_simple_template(name: str, **context) -> str:
    """渲染模板（使用简单的字符串替换）"""
    template = load_template(name)
    for key, value in context.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))
    return template
