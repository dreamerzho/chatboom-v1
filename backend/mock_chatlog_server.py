# mock_chatlog_server.py
# 这是一个模拟的 chatlog 服务器，用于测试后端 API 集成
# 在实际环境中，这个文件会被真实的 chatlog 工具替代

from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import random
import json

app = Flask(__name__)

# 模拟数据
MOCK_CHATROOMS = [
    {"id": "wxid_123456", "name": "建杭良渚外部", "memberCount": 15},
    {"id": "wxid_789012", "name": "星润外部", "memberCount": 12},
    {"id": "wxid_345678", "name": "胤璞内部", "memberCount": 8},
    {"id": "wxid_901234", "name": "项目讨论群", "memberCount": 20},
    {"id": "wxid_567890", "name": "设计团队", "memberCount": 10}
]

MOCK_CONTACTS = [
    {"id": "wxid_user1", "name": "张三", "nickname": "设计师小张"},
    {"id": "wxid_user2", "name": "李四", "nickname": "项目经理李"},
    {"id": "wxid_user3", "name": "王五", "nickname": "开发小王"},
    {"id": "wxid_user4", "name": "赵六", "nickname": "测试小赵"}
]

MOCK_SESSIONS = [
    {"id": "session1", "name": "建杭良渚外部", "lastMessage": "好的，收到", "lastTime": "2024-01-15 14:30:00"},
    {"id": "session2", "name": "星润外部", "lastMessage": "文件已发送", "lastTime": "2024-01-15 13:45:00"},
    {"id": "session3", "name": "胤璞内部", "lastMessage": "会议时间确定", "lastTime": "2024-01-15 12:20:00"}
]

def generate_mock_messages(count=10):
    """生成模拟的聊天记录"""
    messages = []
    message_types = ["1", "3", "34", "49"]  # 文本、图片、语音、文件
    senders = ["张三", "李四", "王五", "赵六"]
    
    for i in range(count):
        msg_type = random.choice(message_types)
        sender = random.choice(senders)
        
        # 生成时间（最近7天内）
        days_ago = random.randint(0, 7)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        timestamp = datetime.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        
        message = {
            "seq": f"msg_{i+1}",
            "senderName": sender,
            "type": msg_type,
            "time": timestamp.isoformat(),
            "content": ""
        }
        
        # 根据消息类型生成内容
        if msg_type == "1":  # 文本
            text_contents = [
                "好的，收到",
                "没问题",
                "正在处理中",
                "请稍等",
                "已完成",
                "有疑问需要确认",
                "文件已发送",
                "会议时间确定"
            ]
            message["content"] = random.choice(text_contents)
        elif msg_type == "3":  # 图片
            message["content"] = "[图片]"
        elif msg_type == "34":  # 语音
            message["content"] = "[语音消息]"
        elif msg_type == "49":  # 文件
            file_names = [
                "设计方案.pdf",
                "项目计划.xlsx",
                "会议纪要.docx",
                "设计稿.psd",
                "代码文件.zip"
            ]
            message["content"] = json.dumps({
                "title": random.choice(file_names),
                "size": random.randint(1024, 10485760)  # 1KB-10MB
            })
        
        messages.append(message)
    
    return messages

@app.route('/api/v1/chatroom', methods=['GET'])
def get_chatrooms():
    """获取群聊列表"""
    return jsonify(MOCK_CHATROOMS)

@app.route('/api/v1/contact', methods=['GET'])
def get_contacts():
    """获取联系人列表"""
    return jsonify(MOCK_CONTACTS)

@app.route('/api/v1/session', methods=['GET'])
def get_sessions():
    """获取会话列表"""
    return jsonify(MOCK_SESSIONS)

@app.route('/api/v1/chatlog', methods=['GET'])
def get_chatlog():
    """获取聊天记录"""
    # 获取查询参数
    talker = request.args.get('talker')
    time_range = request.args.get('time')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    format_type = request.args.get('format', 'json')
    
    # 生成模拟消息
    messages = generate_mock_messages(limit)
    
    # 应用分页
    messages = messages[offset:offset+limit]
    
    if format_type == 'json':
        return jsonify(messages)
    elif format_type == 'csv':
        # 简单的 CSV 格式
        csv_content = "时间,发送者,类型,内容\n"
        for msg in messages:
            csv_content += f"{msg['time']},{msg['senderName']},{msg['type']},{msg['content']}\n"
        return csv_content
    else:
        # 纯文本格式
        text_content = ""
        for msg in messages:
            text_content += f"[{msg['time']}] {msg['senderName']}: {msg['content']}\n"
        return text_content

@app.route('/api/v1/media', methods=['GET'])
def get_media():
    """获取多媒体内容"""
    msgid = request.args.get('msgid')
    
    if not msgid:
        return jsonify({"error": "缺少 msgid 参数"}), 400
    
    # 模拟多媒体内容
    media_content = {
        "msgid": msgid,
        "type": "image",
        "url": f"http://127.0.0.1:5030/media/{msgid}.jpg",
        "size": random.randint(1024, 1048576),
        "filename": f"media_{msgid}.jpg"
    }
    
    return jsonify(media_content)

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取服务状态"""
    return jsonify({
        "status": "running",
        "version": "0.0.15",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def index():
    """根路径"""
    return jsonify({
        "service": "Mock Chatlog Server",
        "version": "0.0.15",
        "description": "这是一个模拟的 chatlog 服务器，用于测试后端 API 集成",
        "endpoints": {
            "status": "/api/status",
            "chatrooms": "/api/v1/chatroom",
            "contacts": "/api/v1/contact",
            "sessions": "/api/v1/session",
            "chatlog": "/api/v1/chatlog",
            "media": "/api/v1/media"
        }
    })

if __name__ == '__main__':
    print("🚀 启动模拟 chatlog 服务器...")
    print("📍 服务地址: http://127.0.0.1:5030")
    print("📋 可用接口:")
    print("   • GET /api/status - 服务状态")
    print("   • GET /api/v1/chatroom - 群聊列表")
    print("   • GET /api/v1/contact - 联系人列表")
    print("   • GET /api/v1/session - 会话列表")
    print("   • GET /api/v1/chatlog - 聊天记录")
    print("   • GET /api/v1/media - 多媒体内容")
    print("按 Ctrl+C 停止服务")
    
    app.run(debug=False, host='0.0.0.0', port=5030) 