#!/usr/bin/env python3
# 检查数据库表结构脚本

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from sqlalchemy import inspect, text
from config import SQLALCHEMY_DATABASE_URI

# 创建Flask应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

def check_table_structure():
    """检查所有表的实际结构"""
    print("=== 检查数据库表结构 ===")
    
    with app.app_context():
        from sqlalchemy import create_engine
        engine = create_engine(SQLALCHEMY_DATABASE_URI)
        inspector = inspect(engine)
        
        # 获取所有表名
        table_names = inspector.get_table_names()
        print(f"数据库中的表：{table_names}")
        
        for table_name in table_names:
            print(f"\n--- {table_name} 表结构 ---")
            columns = inspector.get_columns(table_name)
            for col in columns:
                print(f"  - {col['name']}: {col['type']} (nullable: {col['nullable']})")
            
            # 获取主键信息
            pk = inspector.get_pk_constraint(table_name)
            if pk['constrained_columns']:
                print(f"  主键: {pk['constrained_columns']}")
            
            # 获取外键信息
            fks = inspector.get_foreign_keys(table_name)
            if fks:
                print(f"  外键: {fks}")

def check_chat_messages_sample():
    """检查chat_messages表的样本数据"""
    print("\n=== 检查chat_messages表样本数据 ===")
    
    with app.app_context():
        from sqlalchemy import create_engine, text
        engine = create_engine(SQLALCHEMY_DATABASE_URI)
        
        try:
            # 获取一条样本数据
            result = engine.execute(text("SELECT * FROM chat_messages LIMIT 1"))
            row = result.fetchone()
            if row:
                print("样本数据字段：")
                for key in row._mapping.keys():
                    print(f"  - {key}: {row._mapping[key]}")
            else:
                print("chat_messages表中没有数据")
        except Exception as e:
            print(f"查询失败：{str(e)}")

if __name__ == "__main__":
    check_table_structure()
    check_chat_messages_sample() 