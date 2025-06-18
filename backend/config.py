# 配置文件 config.py
# 用于集中管理后端所有配置信息（如数据库连接参数等）
# 方便后续在不同环境（开发、测试、生产、Docker）下切换

import os

class Config:
    """
    Flask项目的全局配置类。
    支持通过环境变量覆盖默认值，便于Docker和云端部署。
    """
    # 数据库连接参数
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'chattest-db-postgresql.ns-3fzuj6vq.svc')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'mmxwsgg6')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # chatlog工具的API地址
    CHATLOG_API_URL = os.getenv('CHATLOG_API_URL', 'http://192.168.2.1:5030')

    # Flask通用配置
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Chatlog服务配置
# 注意：所有路径严格参照 chatlog 官方文档（chatlog-0.0.15/README.md）
CHATLOG_BASE_URL = 'https://91d2-51-195-241-195.ngrok-free.app'
CHATLOG_API_KEY = os.getenv('CHATLOG_API_KEY', 'your-api-key-here')  # Chatlog API密钥
CHATLOG_API_ENDPOINTS = {
    'chatlog': '/api/v1/chatlog',      # 聊天记录查询（GET /api/v1/chatlog?time=...&talker=...）
    'chatrooms': '/api/v1/chatroom',   # 群聊列表（GET /api/v1/chatroom）
    'contacts': '/api/v1/contact',     # 联系人列表（GET /api/v1/contact）
    'sessions': '/api/v1/session',     # 会话列表（GET /api/v1/session）
    'media': '/api/v1/media'           # 多媒体内容（GET /api/v1/media?msgid=xxx）
}