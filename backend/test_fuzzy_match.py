# 模糊匹配测试工具
# 这个文件用于测试微信昵称和员工姓名的模糊匹配效果

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import find_best_employee_match, clean_nickname, calculate_similarity
from app import db, EmployeeMapping, ChatMessage
from flask import Flask
from config import SQLALCHEMY_DATABASE_URI

# 创建测试用的Flask应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def test_fuzzy_matching():
    """
    测试模糊匹配功能
    """
    with app.app_context():
        # 获取所有员工
        employees = EmployeeMapping.query.all()
        print(f"数据库中员工数量: {len(employees)}")
        
        # 获取所有聊天消息中的发送者
        messages = ChatMessage.query.all()
        sender_names = set(msg.sender_name for msg in messages)
        print(f"聊天记录中的发送者数量: {len(sender_names)}")
        
        print("\n=== 员工映射表 ===")
        for emp in employees:
            print(f"微信昵称: '{emp.wechat_nickname}' -> 真实姓名: '{emp.real_name}' (缩写: {emp.name_abbreviation})")
        
        print("\n=== 聊天记录中的发送者 ===")
        for sender in sorted(sender_names):
            print(f"发送者: '{sender}'")
        
        print("\n=== 模糊匹配结果 ===")
        matched_count = 0
        unmatched_senders = []
        
        for sender in sender_names:
            matched_emp = find_best_employee_match(sender, employees)
            if matched_emp:
                print(f"✓ '{sender}' -> '{matched_emp.real_name}' (微信昵称: '{matched_emp.wechat_nickname}')")
                matched_count += 1
            else:
                print(f"✗ '{sender}' -> 未匹配")
                unmatched_senders.append(sender)
        
        print(f"\n=== 统计结果 ===")
        print(f"总发送者数: {len(sender_names)}")
        print(f"成功匹配数: {matched_count}")
        print(f"未匹配数: {len(unmatched_senders)}")
        print(f"匹配率: {matched_count/len(sender_names)*100:.1f}%")
        
        if unmatched_senders:
            print(f"\n=== 未匹配的发送者 ===")
            for sender in unmatched_senders:
                print(f"'{sender}'")
                # 显示清理后的昵称
                clean_name = clean_nickname(sender)
                print(f"  清理后: '{clean_name}'")
                
                # 显示与所有员工的相似度
                print("  与各员工相似度:")
                for emp in employees:
                    similarity = calculate_similarity(clean_name, clean_nickname(emp.wechat_nickname))
                    print(f"    '{emp.wechat_nickname}' -> {similarity:.3f}")

def test_specific_cases():
    """
    测试特定的匹配案例
    """
    print("\n=== 特定案例测试 ===")
    
    # 测试案例
    test_cases = [
        ("nothing继康", "nothing"),
        ("Super jing 🍒石婧", "Super jing"),
        ("赵婷", "Charlotte"),
        ("nothing", "nothing"),
        ("继康", "nothing"),
    ]
    
    with app.app_context():
        employees = EmployeeMapping.query.all()
        
        for sender, expected_nickname in test_cases:
            matched_emp = find_best_employee_match(sender, employees)
            if matched_emp:
                print(f"✓ '{sender}' -> '{matched_emp.wechat_nickname}' (期望: '{expected_nickname}')")
            else:
                print(f"✗ '{sender}' -> 未匹配 (期望: '{expected_nickname}')")

if __name__ == "__main__":
    print("开始测试模糊匹配功能...")
    test_fuzzy_matching()
    test_specific_cases()
    print("\n测试完成！") 