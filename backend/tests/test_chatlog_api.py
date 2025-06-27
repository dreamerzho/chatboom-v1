#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chatlog API 集成测试脚本
用于测试 chatlog 工具与后端系统的集成是否正常工作
"""

import requests
import json
import sys
from datetime import datetime

# 配置
CHATLOG_API_URL = "http://127.0.0.1:5030"
BACKEND_API_URL = "http://127.0.0.1:5000"

def test_chatlog_direct_api():
    """直接测试 chatlog API"""
    print("🔍 测试 chatlog 直接 API 连接...")
    
    try:
        # 测试群聊列表
        response = requests.get(f"{CHATLOG_API_URL}/api/v1/chatroom", timeout=5)
        print(f"群聊列表 API 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功获取群聊列表，共 {len(data.get('items', []))} 个群聊")
            return True
        else:
            print(f"❌ 群聊列表 API 失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ chatlog API 连接失败: {str(e)}")
        return False

def test_backend_chatlog_integration():
    """测试后端 chatlog 集成"""
    print("\n🔍 测试后端 chatlog 集成...")
    
    try:
        # 测试状态检查
        response = requests.get(f"{BACKEND_API_URL}/api/v1/chatlog/status", timeout=5)
        print(f"状态检查 API 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 后端状态检查成功: {data.get('message', '')}")
        else:
            print(f"❌ 后端状态检查失败: {response.text}")
            return False
        
        # 测试群聊列表
        response = requests.get(f"{BACKEND_API_URL}/api/v1/chatlog/groups", timeout=5)
        print(f"群聊列表 API 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ 后端群聊列表成功，共 {len(data.get('data', []))} 个群聊")
                return True
            else:
                print(f"❌ 后端群聊列表失败: {data.get('error', '')}")
                return False
        else:
            print(f"❌ 后端群聊列表 API 失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 后端集成测试失败: {str(e)}")
        return False

def test_chatlog_messages_api():
    """测试聊天记录 API"""
    print("\n🔍 测试聊天记录 API...")
    
    try:
        # 测试获取聊天记录
        params = {
            'limit': 10,
            'offset': 0,
            'format': 'json'
        }
        response = requests.get(f"{CHATLOG_API_URL}/api/v1/chatlog", params=params, timeout=10)
        print(f"聊天记录 API 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功获取聊天记录，共 {len(data) if isinstance(data, list) else 0} 条")
            return True
        else:
            print(f"❌ 聊天记录 API 失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 聊天记录 API 测试失败: {str(e)}")
        return False

def test_contacts_api():
    """测试联系人 API"""
    print("\n🔍 测试联系人 API...")
    
    try:
        response = requests.get(f"{CHATLOG_API_URL}/api/v1/contact", timeout=5)
        print(f"联系人 API 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功获取联系人列表，共 {len(data.get('items', []))} 个联系人")
            return True
        else:
            print(f"❌ 联系人 API 失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 联系人 API 测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始 chatlog API 集成测试")
    print("=" * 50)
    
    # 测试 chatlog 直接 API
    chatlog_ok = test_chatlog_direct_api()
    
    # 测试聊天记录 API
    messages_ok = test_chatlog_messages_api()
    
    # 测试联系人 API
    contacts_ok = test_contacts_api()
    
    # 测试后端集成
    backend_ok = test_backend_chatlog_integration()
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print(f"chatlog 直接 API: {'✅ 通过' if chatlog_ok else '❌ 失败'}")
    print(f"聊天记录 API: {'✅ 通过' if messages_ok else '❌ 失败'}")
    print(f"联系人 API: {'✅ 通过' if contacts_ok else '❌ 失败'}")
    print(f"后端集成: {'✅ 通过' if backend_ok else '❌ 失败'}")
    
    if all([chatlog_ok, messages_ok, contacts_ok, backend_ok]):
        print("\n🎉 所有测试通过！chatlog API 集成正常工作")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查配置和网络连接")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 