#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chatlog 连接测试脚本
用于检查 chatlog 数据端口是否正常运行
"""

import requests
import json
import sys
import os
from datetime import datetime, timedelta

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_chatlog_connection():
    """测试chatlog连接"""
    
    # chatlog服务地址
    CHATLOG_API_BASE = os.getenv('CHATLOG_API_URL', "http://127.0.0.1:5030")
    
    print("=" * 60)
    print("chatlog 数据端口连接测试")
    print("=" * 60)
    print(f"测试地址: {CHATLOG_API_BASE}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 测试1: 检查服务状态
    print("1. 检查服务状态...")
    try:
        response = requests.get(f"{CHATLOG_API_BASE}/api/v1/chatroom", 
                              params={"format": "json"}, 
                              timeout=10)
        print(f"   状态码: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        
        if response.status_code == 200:
            print("   ✅ 服务响应正常")
            
            # 检查响应内容
            if response.text.strip():
                try:
                    data = response.json()
                    print(f"   ✅ JSON解析成功，返回 {len(data)} 个群聊")
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON解析失败: {e}")
                    print(f"   响应内容预览: {response.text[:200]}...")
            else:
                print("   ⚠️  响应内容为空")
        else:
            print(f"   ❌ 服务响应异常: {response.text[:100]}...")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ 连接失败 - 无法连接到chatlog服务")
        print("   请检查:")
        print("   - chatlog服务是否已启动")
        print("   - 端口5030是否被占用")
        print("   - 防火墙是否阻止了连接")
        return False
    except requests.exceptions.Timeout:
        print("   ❌ 连接超时 - 服务响应时间过长")
        return False
    except Exception as e:
        print(f"   ❌ 连接测试失败: {e}")
        return False
    
    print()
    
    # 测试2: 获取群聊列表
    print("2. 获取群聊列表...")
    try:
        response = requests.get(f"{CHATLOG_API_BASE}/api/v1/chatroom", 
                              params={"format": "json"}, 
                              timeout=10)
        
        if response.status_code == 200 and response.text.strip():
            chatrooms = response.json()
            print(f"   ✅ 成功获取 {len(chatrooms)} 个群聊")
            
            # 显示前5个群聊
            if chatrooms:
                print("   群聊列表预览:")
                for i, room in enumerate(chatrooms[:5]):
                    print(f"   {i+1}. {room.get('name', '未知群聊')} (ID: {room.get('id', 'N/A')})")
                if len(chatrooms) > 5:
                    print(f"   ... 还有 {len(chatrooms) - 5} 个群聊")
            else:
                print("   ⚠️  群聊列表为空")
        else:
            print("   ❌ 获取群聊列表失败")
            
    except Exception as e:
        print(f"   ❌ 获取群聊列表失败: {e}")
    
    print()
    
    # 测试3: 测试聊天记录获取
    print("3. 测试聊天记录获取...")
    try:
        # 先获取群聊列表
        response = requests.get(f"{CHATLOG_API_BASE}/api/v1/chatroom", 
                              params={"format": "json"}, 
                              timeout=10)
        
        if response.status_code == 200 and response.text.strip():
            chatrooms = response.json()
            
            if chatrooms:
                # 使用第一个群聊进行测试
                test_room = chatrooms[0]
                room_name = test_room.get('name', '测试群聊')
                
                print(f"   使用群聊 '{room_name}' 进行测试...")
                
                # 获取最近7天的聊天记录
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                
                chatlog_url = f"{CHATLOG_API_BASE}/api/v1/chatlog"
                params = {
                    "talker": room_name,
                    "time": f"{start_date}~{end_date}",
                    "format": "json"
                }
                
                response = requests.get(chatlog_url, params=params, timeout=30)
                print(f"   请求URL: {response.url}")
                print(f"   状态码: {response.status_code}")
                
                if response.status_code == 200:
                    if response.text.strip():
                        try:
                            chatlog = response.json()
                            print(f"   ✅ 成功获取 {len(chatlog)} 条聊天记录")
                            
                            # 统计消息类型
                            msg_types = {}
                            for msg in chatlog:
                                msg_type = msg.get('type', 'unknown')
                                msg_types[msg_type] = msg_types.get(msg_type, 0) + 1
                            
                            print("   消息类型统计:")
                            for msg_type, count in msg_types.items():
                                type_names = {
                                    1: "文本消息",
                                    3: "图片消息",
                                    49: "文件消息",
                                    34: "语音消息",
                                    43: "视频消息"
                                }
                                type_name = type_names.get(msg_type, f"类型{msg_type}")
                                print(f"   - {type_name}: {count} 条")
                                
                        except json.JSONDecodeError as e:
                            print(f"   ❌ JSON解析失败: {e}")
                            print(f"   响应内容预览: {response.text[:200]}...")
                    else:
                        print("   ⚠️  聊天记录为空")
                else:
                    print(f"   ❌ 获取聊天记录失败: {response.text[:100]}...")
            else:
                print("   ⚠️  没有可用的群聊进行测试")
        else:
            print("   ❌ 无法获取群聊列表进行测试")
            
    except Exception as e:
        print(f"   ❌ 测试聊天记录获取失败: {e}")
    
    print()
    
    # 测试4: 检查其他API端点
    print("4. 检查其他API端点...")
    
    endpoints = [
        ("/api/v1/contact", "联系人列表"),
        ("/api/v1/session", "会话列表"),
        ("/api/v1/status", "服务状态")
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{CHATLOG_API_BASE}{endpoint}", 
                                  params={"format": "json"}, 
                                  timeout=5)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"   {status} {description}: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {description}: 连接失败")
    
    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    test_chatlog_connection() 