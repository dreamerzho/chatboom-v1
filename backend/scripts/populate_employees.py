# -*- coding: utf-8 -*-
"""
一个用于填充初始员工数据的脚本。
"""
import sys
import os
from contextlib import contextmanager

# 将项目根目录添加到Python路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.employee import EmployeeMapping
from db import db

@contextmanager
def app_context():
    """提供应用上下文的上下文管理器。"""
    app = create_app()
    with app.app_context():
        yield

def populate_employees():
    """
    填充员工数据到数据库。
    如果员工已存在（基于姓名或微信昵称），则跳过。
    """
    employees_to_add = [
        {'real_name': '谢建锋', 'position': '项目经理', 'wechat_nickname': '谢建锋（长颈鹿）', 'name_abbreviation': 'xjf'},
        {'real_name': '赵继康', 'position': '项目经理', 'wechat_nickname': 'nothing', 'name_abbreviation': 'zjk'},
        {'real_name': '崔莲', 'position': '项目经理', 'wechat_nickname': 'Vicky软三胖', 'name_abbreviation': 'cl'},
        {'real_name': '殷琳', 'position': 'AE', 'wechat_nickname': 'Charlotte', 'name_abbreviation': 'yl'},
        {'real_name': '苏星星', 'position': 'AE', 'wechat_nickname': 'XiaoXiaoSu1996a', 'name_abbreviation': 'sxx'},
        {'real_name': '吴昱达', 'position': '文案', 'wechat_nickname': '特里同', 'name_abbreviation': 'wyd'},
        {'real_name': '后博寒', 'position': '文案总监', 'wechat_nickname': '西蒙', 'name_abbreviation': 'hbh'},
        {'real_name': '周康', 'position': '设计', 'wechat_nickname': '旺旺脆脆冰。', 'name_abbreviation': 'zk'},
        {'real_name': '毛晓慧', 'position': '设计总监', 'wechat_nickname': '阿得', 'name_abbreviation': 'mxh'},
        {'real_name': '马萌', 'position': '外包文案', 'wechat_nickname': 'mm-placeholder', 'name_abbreviation': 'mm'},
        {'real_name': '刘鉴辉', 'position': '外包设计', 'wechat_nickname': 'Lt.', 'name_abbreviation': 'ljh'},
        {'real_name': '王威凯', 'position': '外包视频', 'wechat_nickname': 'wwk-placeholder', 'name_abbreviation': 'wwk'},
        {'real_name': '赵彬彬', 'position': '外包视频', 'wechat_nickname': 'zbb-placeholder', 'name_abbreviation': 'zbb'},
    ]

    with app_context():
        print("开始填充员工数据...")
        added_count = 0
        skipped_count = 0
        
        for emp_data in employees_to_add:
            # 检查员工是否已存在
            existing = EmployeeMapping.query.filter(
                (EmployeeMapping.real_name == emp_data['real_name']) | 
                (EmployeeMapping.wechat_nickname == emp_data['wechat_nickname']) if emp_data['wechat_nickname'] else False
            ).first()
            
            if existing:
                print(f"员工 '{emp_data['real_name']}' 或昵称 '{emp_data['wechat_nickname']}' 已存在, 跳过。")
                skipped_count += 1
                continue

            new_employee = EmployeeMapping(**emp_data)
            db.session.add(new_employee)
            added_count += 1
            print(f"准备添加员工: {emp_data['real_name']}")

        if added_count > 0:
            db.session.commit()
            print(f"\n成功添加 {added_count} 名新员工。")
        else:
            print("\n没有新员工需要添加。")
            
        print(f"跳过 {skipped_count} 名已存在的员工。")
        print("数据填充完成。")

if __name__ == '__main__':
    populate_employees() 