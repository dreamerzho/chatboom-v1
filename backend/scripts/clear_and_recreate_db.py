#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键清空所有表并重建数据库结构的自动化脚本（开发环境专用）
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.app import app
from backend.db import db

def clear_and_recreate_db():
    with app.app_context():
        print('开始删除所有表...')
        db.drop_all()
        print('所有表已删除。')
        print('开始重建所有表...')
        db.create_all()
        print('所有表已重建完成！')

if __name__ == '__main__':
    clear_and_recreate_db() 