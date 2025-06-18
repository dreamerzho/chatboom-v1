#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chatlog 连接测试脚本
用于测试 chatlog 服务的连接状态和响应格式
"""

import requests
import json
import sys
from datetime import datetime

def test_chatlog_connection():
    """测试 chatlog 服务连接"""
    
    # 测试的URL列表
    test_urls = [
        "http://127.0.0.1:5030",
        "http://localhost:5030",
        "https://91d2-51-195-241-195.ngrok-free.app"  # 之前的ngrok地址
    ]
    
    print("=" * 60)
    print("chatlog 服务连接测试")
    print("=" * 60)
    
    for base_url in test_urls:
        print(f"\n测试地址: {base_url}")
        print("-" * 40)
        
        try:
            # 测试1: 检查服务状态
            status_url = f"{base_url}/api/v1/chatroom"
            print(f"1. 检查服务状态: {status_url}")
            
            response = requests.get(status_url, timeout=10)
            print(f"   状态码: {response.status_code}")
            print(f"   响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                print(f"   响应内容长度: {len(response.text)}")
                print(f"   响应内容预览: {response.text[:200]}...")
                
                # 尝试解析JSON
                try:
                    data = response.json()
                    print(f"   JSON解析成功，数据类型: {type(data)}")
                    if isinstance(data, list):
                        print(f"   群聊数量: {len(data)}")
                        if data:
                            print(f"   第一个群聊: {data[0]}")
                except json.JSONDecodeError as e:
                    print(f"   JSON解析失败: {e}")
            else:
                print(f"   错误响应: {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError as e:
            print(f"   连接错误: {e}")
        except requests.exceptions.Timeout as e:
            print(f"   超时错误: {e}")
        except Exception as e:
            print(f"   其他错误: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_chatlog_connection() 