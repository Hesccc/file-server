"""
工具函数模块
"""
from .template import render_simple_template, load_template, get_template_path
from .file import fbytes, get_file_icon

__all__ = ['render_simple_template', 'load_template', 'get_template_path', 'fbytes', 'get_file_icon']
