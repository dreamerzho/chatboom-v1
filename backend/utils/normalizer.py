# 归一化工具：项目、员工、群聊名称/ID标准化
# 用于所有数据入库前的唯一性、规范性处理

import re
from typing import Optional, Dict, List
from backend.models.project import Project, ProjectChatroom
from backend.models.employee import EmployeeMapping
from backend.db import db

class Normalizer:
    @staticmethod
    def normalize_project_name(name: str) -> Optional[int]:
        """项目名称归一化为唯一ID，去空格、统一大小写，支持模糊查找"""
        if not name:
            return None
        norm = name.strip().lower()
        project = Project.query.filter(db.func.lower(Project.project_name) == norm).first()
        if project:
            return project.id
        # 模糊查找
        project = Project.query.filter(Project.project_name.ilike(f"%{norm}%")).first()
        if project:
            return project.id
        return None

    @staticmethod
    def normalize_employee(name: str) -> Optional[int]:
        """员工昵称/姓名归一化为唯一ID，支持多字段、去空格、统一大小写、模糊查找"""
        if not name:
            return None
        norm = name.strip().lower()
        # 先精确查找
        emp = EmployeeMapping.query.filter(
            (db.func.lower(EmployeeMapping.wechat_nickname) == norm) |
            (db.func.lower(EmployeeMapping.real_name) == norm) |
            (db.func.lower(EmployeeMapping.name_abbreviation) == norm)
        ).first()
        if emp:
            return emp.id
        # 模糊查找
        emp = EmployeeMapping.query.filter(
            (EmployeeMapping.wechat_nickname.ilike(f"%{norm}%")) |
            (EmployeeMapping.real_name.ilike(f"%{norm}%")) |
            (EmployeeMapping.name_abbreviation.ilike(f"%{norm}%"))
        ).first()
        if emp:
            return emp.id
        return None

    @staticmethod
    def normalize_chatroom(name: str) -> Optional[str]:
        """群聊名称归一化为唯一ID，支持精确/模糊查找，返回chatroom_id"""
        if not name:
            return None
        norm = name.strip().lower()
        chatroom = ProjectChatroom.query.filter(db.func.lower(ProjectChatroom.chatroom_name) == norm).first()
        if chatroom:
            return chatroom.chatroom_id
        # 模糊查找
        chatroom = ProjectChatroom.query.filter(ProjectChatroom.chatroom_name.ilike(f"%{norm}%")).first()
        if chatroom:
            return chatroom.chatroom_id
        return None

    @staticmethod
    def normalize_str(s: str) -> str:
        """通用字符串归一化：去空格、统一大小写、去除特殊字符"""
        if not s:
            return ''
        s = s.strip().lower()
        s = re.sub(r'[\s\t\n\r]+', '', s)
        return s 