#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 chatlog 接口格式的脚本
验证请求参数和响应格式是否符合官方规范
"""

import requests
import json
from urllib.parse import urlencode

def test_chatlog_format():
    """测试 chatlog 接口的请求格式"""
    
    # chatlog 服务地址
    base_url = "http://127.0.0.1:5030"
    
    print("=== 测试 chatlog 接口格式 ===")
    
    # 测试1: 群聊列表接口
    print("\n1. 测试群聊列表接口")
    try:
        response = requests.get(f"{base_url}/api/v1/chatroom")
        print(f"状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        if response.status_code == 200:
            data = response.json()
            print(f"群聊数量: {len(data)}")
            if data:
                print(f"第一个群聊: {data[0].get('nickName', 'N/A')}")
        else:
            print(f"错误响应: {response.text[:200]}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试2: 聊天记录接口 - 使用你提供的参数
    print("\n2. 测试聊天记录接口（使用你的参数）")
    try:
        params = {
            "time": "2025-05-01~2025-05-26",
            "talker": "越城天地&巨象微信工作群",
            "format": "json"
        }
        
        # 构建 URL
        url = f"{base_url}/api/v1/chatlog"
        print(f"请求URL: {url}")
        print(f"请求参数: {params}")
        
        # 发送请求
        response = requests.get(url, params=params)
        print(f"状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"实际请求URL: {response.url}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"聊天记录数量: {len(data)}")
            if data:
                print(f"第一条记录: {data[0]}")
        else:
            print(f"错误响应: {response.text[:200]}")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试3: 验证我们的集成代码
    print("\n3. 测试我们的集成代码")
    try:
        from chatlog_integration import ChatlogIntegration
        
        chatlog = ChatlogIntegration()
        
        # 测试服务状态
        status = chatlog.check_service_status()
        print(f"服务状态: {status}")
        
        # 测试获取群聊列表
        chatrooms = chatlog.get_chatrooms()
        print(f"集成代码获取群聊数量: {len(chatrooms)}")
        
        # 测试获取聊天记录
        chatlog_data = chatlog.get_chatlog_by_talker_and_time(
            talker="越城天地&巨象微信工作群",
            start_date="2025-05-01",
            end_date="2025-05-26"
        )
        print(f"集成代码获取聊天记录数量: {len(chatlog_data)}")
        
    except Exception as e:
        print(f"集成代码测试失败: {e}")

if __name__ == "__main__":
    test_chatlog_format() 