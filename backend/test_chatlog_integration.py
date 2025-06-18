# chatlog集成功能测试脚本
# 这个脚本用于测试chatlog工具的集成功能

import requests
import json
import time
from datetime import datetime

# 后端服务地址
BACKEND_URL = "http://localhost:5000"

def test_chatlog_status():
    """
    测试chatlog状态检查功能
    """
    print("=== 测试chatlog状态检查 ===")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/chatlog/status")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

def test_chatlog_groups():
    """
    测试获取群聊列表功能
    """
    print("\n=== 测试获取群聊列表 ===")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/chatlog/groups")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

def test_chatlog_stats():
    """
    测试聊天记录统计功能
    """
    print("\n=== 测试聊天记录统计 ===")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/chatlog/stats")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

def test_chatlog_messages():
    """
    测试获取聊天记录功能
    """
    print("\n=== 测试获取聊天记录 ===")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/chatlog/messages?page=1&per_page=10")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

def test_sync_chatlog_data():
    """
    测试同步聊天记录功能
    """
    print("\n=== 测试同步聊天记录 ===")
    
    try:
        # 注意：这个测试需要chatlog工具实际运行
        data = {
            "group_name": "测试群聊",
            "days_back": 1
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/v1/chatlog/sync",
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

def test_chatlog_chatrooms():
    """
    测试获取群聊列表
    """
    print("\n" + "=" * 50)
    print("测试获取群聊列表...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/chatlog/chatrooms")
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('success'):
            print(f"✅ 成功获取到 {result.get('count', 0)} 个群聊")
            return True
        else:
            print("❌ 获取群聊列表失败")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_chatlog_contacts():
    """
    测试获取联系人列表
    """
    print("\n" + "=" * 50)
    print("测试获取联系人列表...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/chatlog/contacts")
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('success'):
            print(f"✅ 成功获取到 {result.get('count', 0)} 个联系人")
            return True
        else:
            print("❌ 获取联系人列表失败")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_chatlog_sessions():
    """
    测试获取会话列表
    """
    print("\n" + "=" * 50)
    print("测试获取会话列表...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/chatlog/sessions")
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('success'):
            print(f"✅ 成功获取到 {result.get('count', 0)} 个会话")
            return True
        else:
            print("❌ 获取会话列表失败")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_chatlog_recent():
    """
    测试获取最近聊天记录
    """
    print("\n" + "=" * 50)
    print("测试获取最近聊天记录...")
    
    try:
        params = {'days': 3}
        response = requests.get(f"{BACKEND_URL}/api/v1/chatlog/recent", params=params)
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"查询参数: {params}")
        print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('success'):
            print(f"✅ 成功获取到 {result.get('count', 0)} 条最近聊天记录")
            return True
        else:
            print("❌ 获取最近聊天记录失败")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_chatlog_sync():
    """
    测试同步聊天记录
    """
    print("\n" + "=" * 50)
    print("测试同步聊天记录...")
    
    try:
        response = requests.post(f"{BACKEND_URL}/api/v1/chatlog/sync")
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if result.get('success'):
            print("✅ 同步聊天记录成功")
            return True
        else:
            print("❌ 同步聊天记录失败")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def main():
    """
    主测试函数
    """
    print("开始测试chatlog集成功能...")
    print(f"后端服务地址: {BACKEND_URL}")
    
    # 测试结果统计
    test_results = []
    
    # 执行测试
    test_results.append(("状态检查", test_chatlog_status()))
    test_results.append(("群聊列表", test_chatlog_groups()))
    test_results.append(("聊天统计", test_chatlog_stats()))
    test_results.append(("聊天记录", test_chatlog_messages()))
    test_results.append(("数据同步", test_sync_chatlog_data()))
    test_results.append(("获取群聊列表", test_chatlog_chatrooms()))
    test_results.append(("获取联系人列表", test_chatlog_contacts()))
    test_results.append(("获取会话列表", test_chatlog_sessions()))
    test_results.append(("获取最近聊天记录", test_chatlog_recent()))
    test_results.append(("同步聊天记录", test_chatlog_sync()))
    
    # 输出测试结果
    print("\n" + "="*50)
    print("测试结果汇总:")
    print("="*50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！")
    else:
        print("⚠️  部分测试失败，请检查相关功能")

if __name__ == "__main__":
    main() 