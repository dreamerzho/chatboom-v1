#!/usr/bin/env python3
# 测试Chatlog配置脚本

import requests
import json
from config import CHATLOG_BASE_URL, CHATLOG_API_ENDPOINTS

def test_chatlog_direct():
    """直接测试Chatlog服务"""
    print("=== 直接测试Chatlog服务 ===")
    
    try:
        # 测试聊天记录API（使用正确的格式）
        params = {
            'time': '2025-06-01~2025-06-17',
            'limit': '5',
            'format': 'json'
        }
        chatlog_url = f"{CHATLOG_BASE_URL}{CHATLOG_API_ENDPOINTS['chatlog']}"
        print(f"测试聊天记录API: {chatlog_url}")
        print(f"参数: {params}")
        
        response = requests.get(chatlog_url, params=params, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json() if response.text else []
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

def test_chatlog_via_backend():
    """通过后端测试Chatlog服务"""
    print("\n=== 通过后端测试Chatlog服务 ===")
    
    try:
        # 测试后端Chatlog状态API
        backend_url = "http://localhost:5000/api/v1/chatlog/status"
        print(f"测试后端API: {backend_url}")
        
        response = requests.get(backend_url, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

def test_chatlog_endpoints():
    """测试所有Chatlog端点"""
    print("\n=== 测试所有Chatlog端点 ===")
    
    endpoints = [
        'chatrooms',
        'contacts', 
        'sessions'
    ]
    
    for endpoint in endpoints:
        try:
            url = f"{CHATLOG_BASE_URL}{CHATLOG_API_ENDPOINTS[endpoint]}"
            print(f"\n测试 {endpoint}: {url}")
            
            response = requests.get(url, timeout=10)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json() if response.text else []
                if isinstance(data, list):
                    print(f"返回 {len(data)} 条记录")
                    if len(data) > 0:
                        print(f"示例数据: {json.dumps(data[0], indent=2, ensure_ascii=False)}")
                elif isinstance(data, dict):
                    print(f"返回数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                print(f"请求失败: {response.text}")
                
        except Exception as e:
            print(f"测试失败: {str(e)}")

def test_specific_chatlog():
    """测试特定的聊天记录查询"""
    print("\n=== 测试特定聊天记录查询 ===")
    
    try:
        # 使用您提供的示例参数
        params = {
            'time': '2025-06-01~2025-06-26',
            'talker': '越城天地&巨象微信工作群',
            'format': 'json'
        }
        
        url = f"{CHATLOG_BASE_URL}{CHATLOG_API_ENDPOINTS['chatlog']}"
        print(f"测试特定群聊: {url}")
        print(f"参数: {params}")
        
        response = requests.get(url, params=params, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json() if response.text else []
            print(f"返回 {len(data) if isinstance(data, list) else 0} 条记录")
            if isinstance(data, list) and len(data) > 0:
                print(f"示例记录: {json.dumps(data[0], indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("🔍 Chatlog配置测试")
    print("=" * 50)
    print(f"Chatlog基础URL: {CHATLOG_BASE_URL}")
    print(f"API端点配置: {json.dumps(CHATLOG_API_ENDPOINTS, indent=2, ensure_ascii=False)}")
    print("=" * 50)
    
    # 测试直接访问
    direct_ok = test_chatlog_direct()
    
    # 测试通过后端访问
    backend_ok = test_chatlog_via_backend()
    
    # 测试其他端点
    test_chatlog_endpoints()
    
    # 测试特定聊天记录查询
    specific_chatlog_ok = test_specific_chatlog()
    
    # 总结
    print("\n" + "=" * 50)
    print("📋 测试总结：")
    
    if direct_ok:
        print("✅ 直接访问Chatlog：成功")
    else:
        print("❌ 直接访问Chatlog：失败")
    
    if backend_ok:
        print("✅ 通过后端访问Chatlog：成功")
    else:
        print("❌ 通过后端访问Chatlog：失败")
    
    if direct_ok and backend_ok and specific_chatlog_ok:
        print("\n🎉 Chatlog配置完全正常！")
        print("💡 可以开始数据同步和功能开发")
    else:
        print("\n⚠️ Chatlog配置存在问题")
        print("💡 请检查网络连接和服务状态")

if __name__ == "__main__":
    main() 