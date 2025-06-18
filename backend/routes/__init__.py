# API路由包
# 包含所有API路由定义，按功能模块拆分

from .employees import employees_bp
from .projects import projects_bp
from .files import files_bp
from .dashboard import dashboard_bp
from .chatlog import chatlog_bp

__all__ = [
    'employees_bp',
    'projects_bp', 
    'files_bp',
    'dashboard_bp',
    'chatlog_bp'
] 