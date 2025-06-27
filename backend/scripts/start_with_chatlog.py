# start_with_chatlog.py
# 这个脚本用于启动后端服务并测试 chatlog 集成功能

import os
import sys
import time
import requests
from datetime import datetime

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_chatlog_service():
    """
    检查 chatlog 服务是否可用
    """
    print("🔍 检查 chatlog 服务状态...")
    
    try:
        # 直接检查 chatlog 服务
        response = requests.get("http://127.0.0.1:5030/api/v1/chatroom", timeout=5)
        if response.status_code == 200:
            print("✅ chatlog 服务运行正常")
            return True
        else:
            print(f"⚠️  chatlog 服务响应异常，状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到 chatlog 服务，请确保服务已启动")
        print("   启动命令: chatlog server")
        return False
    except Exception as e:
        print(f"❌ 检查 chatlog 服务时发生错误: {str(e)}")
        return False

def test_backend_chatlog_apis():
    """
    测试后端的 chatlog 相关 API
    """
    print("\n🧪 测试后端 chatlog API...")
    
    base_url = "http://127.0.0.1:5000"
    
    # 测试服务状态
    try:
        response = requests.get(f"{base_url}/api/v1/chatlog/status")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 后端 chatlog 状态检查: {result.get('status', 'unknown')}")
        else:
            print(f"❌ 后端 chatlog 状态检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 后端 chatlog 状态检查异常: {str(e)}")
    
    # 测试获取群聊列表
    try:
        response = requests.get(f"{base_url}/api/v1/chatlog/chatrooms")
        if response.status_code == 200:
            result = response.json()
            count = result.get('count', 0)
            print(f"✅ 获取群聊列表: {count} 个群聊")
        else:
            print(f"❌ 获取群聊列表失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取群聊列表异常: {str(e)}")
    
    # 测试获取最近聊天记录
    try:
        response = requests.get(f"{base_url}/api/v1/chatlog/recent?days=1")
        if response.status_code == 200:
            result = response.json()
            count = result.get('count', 0)
            print(f"✅ 获取最近聊天记录: {count} 条消息")
        else:
            print(f"❌ 获取最近聊天记录失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取最近聊天记录异常: {str(e)}")

def main():
    """
    主函数
    """
    print("=" * 60)
    print("🚀 广告公司服务监测系统 - Chatlog 集成测试")
    print("=" * 60)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查 chatlog 服务
    chatlog_available = check_chatlog_service()
    
    if not chatlog_available:
        print("\n⚠️  提示:")
        print("1. 请先启动 chatlog 服务:")
        print("   chatlog server")
        print("2. 确保 chatlog 服务运行在 http://127.0.0.1:5030")
        print("3. 然后重新运行此脚本")
        return
    
    # 启动后端服务
    print("\n🚀 启动后端服务...")
    print("后端服务将在 http://127.0.0.1:5000 启动")
    print("按 Ctrl+C 停止服务")
    
    # 等待服务启动
    time.sleep(2)
    
    # 测试后端 API
    test_backend_chatlog_apis()
    
    print("\n📋 可用的 API 接口:")
    print("• GET  /api/v1/chatlog/status     - 检查服务状态")
    print("• GET  /api/v1/chatlog/chatrooms  - 获取群聊列表")
    print("• GET  /api/v1/chatlog/contacts   - 获取联系人列表")
    print("• GET  /api/v1/chatlog/sessions   - 获取会话列表")
    print("• GET  /api/v1/chatlog/messages   - 获取聊天记录")
    print("• GET  /api/v1/chatlog/recent     - 获取最近聊天记录")
    print("• POST /api/v1/chatlog/sync       - 同步聊天记录")
    
    print("\n🔗 测试链接:")
    print("• 服务状态: http://127.0.0.1:5000/api/v1/chatlog/status")
    print("• 群聊列表: http://127.0.0.1:5000/api/v1/chatlog/chatrooms")
    print("• 最近记录: http://127.0.0.1:5000/api/v1/chatlog/recent?days=3")
    
    print("\n💡 提示:")
    print("• 可以在浏览器中访问上述链接查看 API 响应")
    print("• 使用 Postman 或 curl 进行更详细的测试")
    print("• 运行 python test_chatlog_integration.py 进行完整测试")
    
    # 启动 Flask 应用
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"\n❌ 启动服务失败: {str(e)}")

if __name__ == "__main__":
    main() 