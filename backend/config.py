# 配置文件 config.py
# 用于集中管理后端所有配置信息（如数据库连接参数、API密钥等）
# 支持多环境切换（开发/测试/生产），并通过环境变量灵活配置
# 启动时可自动校验关键配置项，防止配置遗漏

import os

class Config:
    """
    Flask项目的全局配置类。
    支持通过环境变量覆盖默认值，便于Docker、云端和本地多环境部署。
    """
    # 数据库配置 - 统一使用PostgreSQL，所有参数均可用环境变量覆盖
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', '127.0.0.1')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '123456')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')
    
    # 生成SQLAlchemy/PostgreSQL连接字符串
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Chatlog服务配置
    CHATLOG_BASE_URL = os.getenv('CHATLOG_BASE_URL', 'http://127.0.0.1:5030')
    CHATLOG_API_KEY = os.getenv('CHATLOG_API_KEY', 'your-api-key-here')  # Chatlog API密钥
    CHATLOG_API_ENDPOINTS = {
        'chatlog': '/api/v1/chatlog',      # 聊天记录查询
        'chatrooms': '/api/v1/chatroom',  # 群聊列表
        'contacts': '/api/v1/contact',    # 联系人列表
        'sessions': '/api/v1/session',    # 会话列表
        'media': '/api/v1/media'          # 多媒体内容
    }

    # Flask通用配置
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

    # 其他可扩展配置项
    ENV = os.getenv('ENV', 'development')  # 当前环境：development/production/test
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def validate(cls):
        """
        校验关键配置项，启动时调用。缺失则抛出异常。
        """
        required = [
            ('POSTGRES_HOST', cls.POSTGRES_HOST),
            ('POSTGRES_USER', cls.POSTGRES_USER),
            ('POSTGRES_PASSWORD', cls.POSTGRES_PASSWORD),
            ('POSTGRES_DB', cls.POSTGRES_DB),
            ('SECRET_KEY', cls.SECRET_KEY)
        ]
        missing = [name for name, value in required if not value]
        if missing:
            raise RuntimeError(f"缺少关键配置项: {', '.join(missing)}，请检查环境变量或config.py")