# 调试启动脚本 - 用于诊断后端启动问题
# 按照报告要求，逐步检查各个组件

import sys
import os

def check_python_environment():
    """检查Python环境"""
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"当前工作目录: {os.getcwd()}")

def check_dependencies():
    """检查关键依赖"""
    try:
        import flask
        print(f"✓ Flask版本: {flask.__version__}")
    except ImportError as e:
        print(f"✗ Flask导入失败: {e}")
    
    try:
        import psutil
        print("✓ psutil导入成功")
    except ImportError as e:
        print(f"✗ psutil导入失败: {e}")
    
    try:
        import psycopg2
        print("✓ psycopg2导入成功")
    except ImportError as e:
        print(f"✗ psycopg2导入失败: {e}")

def check_database_connection():
    """检查数据库连接"""
    try:
        from config import Config
        print(f"数据库URI: {Config.SQLALCHEMY_DATABASE_URI}")
        
        import psycopg2
        conn = psycopg2.connect(
            host=Config.POSTGRES_HOST,
            port=Config.POSTGRES_PORT,
            user=Config.POSTGRES_USER,
            password=Config.POSTGRES_PASSWORD,
            database=Config.POSTGRES_DB
        )
        print("✓ 数据库连接成功")
        conn.close()
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")

def check_app_creation():
    """检查应用创建"""
    try:
        from app import create_app
        app = create_app()
        print("✓ Flask应用创建成功")
        return app
    except Exception as e:
        print(f"✗ Flask应用创建失败: {e}")
        return None

if __name__ == "__main__":
    print("=== 后端环境诊断 ===")
    check_python_environment()
    print("\n=== 依赖检查 ===")
    check_dependencies()
    print("\n=== 数据库连接检查 ===")
    check_database_connection()
    print("\n=== 应用创建检查 ===")
    app = check_app_creation()
    
    if app:
        print("\n=== 启动Flask服务 ===")
        try:
            app.run(host='0.0.0.0', port=5000, debug=True)
        except Exception as e:
            print(f"✗ 服务启动失败: {e}") 