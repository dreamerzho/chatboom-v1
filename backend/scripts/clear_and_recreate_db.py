#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键清空所有表并重建数据库结构的自动化脚本（开发环境专用）
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.app import create_app
from backend.db import db
from sqlalchemy import text

def clear_and_recreate_db():
    app = create_app()
    with app.app_context():
        # 依赖顺序：先删子表再删主表
        tables = [
            'keyword_analyses',
            'risk_events',
            'workload_records',
            'chat_messages',
            'assets',
            'file_records',
            'project_chatrooms',
            'project_summary',
            'projects',
            'employee_mappings',
        ]
        for table in tables:
            db.session.execute(text(f'TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;'))
        db.session.commit()
        db.create_all()
        print('数据库核心表已全部清空并重建！')

if __name__ == '__main__':
    clear_and_recreate_db() 