#!/usr/bin/env python3
# 系统状态检查脚本
# 用于快速验证数据库、API和前端状态

import sys
import os
import requests
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from sqlalchemy import func
from config import SQLALCHEMY_DATABASE_URI
from app import db, EmployeeMapping, Project, FileRecord, ChatMessage

# 创建Flask应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def check_database_status():
    """检查数据库状态"""
    print("=== 数据库状态检查 ===")
    
    with app.app_context():
        try:
            # 检查表记录数
            employee_count = db.session.query(func.count(EmployeeMapping.id)).scalar()
            project_count = db.session.query(func.count(Project.id)).scalar()
            file_count = db.session.query(func.count(FileRecord.id)).scalar()
            message_count = db.session.query(func.count(ChatMessage.id)).scalar()
            
            print(f"✅ 数据库连接正常")
            print(f"📊 数据统计：")
            print(f"   - 员工映射：{employee_count} 条")
            print(f"   - 项目信息：{project_count} 条")
            print(f"   - 文件记录：{file_count} 条")
            print(f"   - 聊天消息：{message_count} 条")
            
            return True
        except Exception as e:
            print(f"❌ 数据库检查失败：{str(e)}")
            return False

def check_api_status():
    """检查API状态"""
    print("\n=== API状态检查 ===")
    
    try:
        # 检查后端API
        base_url = "http://localhost:5000"
        
        # 健康检查
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端API健康检查通过")
        else:
            print(f"❌ 后端API健康检查失败：{response.status_code}")
            return False
        
        # 检查主要API端点
        endpoints = [
            "/api/v1/employees",
            "/api/v1/projects", 
            "/api/v1/files/list",
            "/api/v1/dashboard/stats"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {endpoint} - 正常")
                else:
                    print(f"❌ {endpoint} - 失败 ({response.status_code})")
            except Exception as e:
                print(f"❌ {endpoint} - 连接失败：{str(e)}")
        
        return True
    except Exception as e:
        print(f"❌ API检查失败：{str(e)}")
        return False

def check_frontend_status():
    """检查前端状态"""
    print("\n=== 前端状态检查 ===")
    
    try:
        # 检查前端服务
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ 前端服务正常运行")
            return True
        else:
            print(f"❌ 前端服务异常：{response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 前端检查失败：{str(e)}")
        return False

def check_chatlog_status():
    """检查chatlog状态"""
    print("\n=== Chatlog状态检查 ===")
    
    try:
        # 检查chatlog API
        response = requests.get("http://localhost:5000/api/v1/chatlog/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Chatlog API响应正常")
            print(f"📊 Chatlog状态：{data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Chatlog API检查失败：{response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Chatlog检查失败：{str(e)}")
        return False

def generate_status_report():
    """生成状态报告"""
    print("🔍 系统状态检查报告")
    print("=" * 50)
    print(f"检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 执行各项检查
    db_ok = check_database_status()
    api_ok = check_api_status()
    frontend_ok = check_frontend_status()
    chatlog_ok = check_chatlog_status()
    
    # 生成总结
    print("\n" + "=" * 50)
    print("📋 检查总结：")
    
    if db_ok:
        print("✅ 数据库：正常")
    else:
        print("❌ 数据库：异常")
    
    if api_ok:
        print("✅ 后端API：正常")
    else:
        print("❌ 后端API：异常")
    
    if frontend_ok:
        print("✅ 前端服务：正常")
    else:
        print("❌ 前端服务：异常")
    
    if chatlog_ok:
        print("✅ Chatlog：正常")
    else:
        print("❌ Chatlog：异常")
    
    # 总体状态
    if all([db_ok, api_ok, frontend_ok]):
        print("\n🎉 系统整体状态：正常")
        print("💡 建议：可以开始数据导入和功能测试")
    else:
        print("\n⚠️ 系统状态：部分异常")
        print("💡 建议：先解决异常问题，再进行后续开发")
    
    return all([db_ok, api_ok, frontend_ok])

if __name__ == "__main__":
    generate_status_report() 