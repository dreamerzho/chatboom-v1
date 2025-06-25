# 广告公司服务监测软件 - 后端主应用文件
# 这个文件是Flask应用的核心，负责应用初始化、数据库连接和路由注册

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

import os
from datetime import datetime
import logging
# from config import SQLALCHEMY_DATABASE_URI # 移除直接导入，通过 app.config 访问
from db import db
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    # 允许所有来源的跨域请求，这在开发环境中是安全的
    CORS(app, supports_credentials=True)
    app.config.from_object(Config)  # 直接传Config类对象
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app) # 初始化 db

    # 注册蓝图
    from models import EmployeeMapping, Project, FileRecord, ChatMessage, ProjectChatroom, KeywordCategory

    # 导入API路由蓝图
    from routes import employees_bp, projects_bp, files_bp, dashboard_bp, chatlog_bp, sync_bp, keywords_bp
    from routes.unmatched import unmatched_bp
    from routes.workload import workload_bp
    app.register_blueprint(employees_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(chatlog_bp)
    app.register_blueprint(sync_bp)
    app.register_blueprint(keywords_bp)
    app.register_blueprint(unmatched_bp)
    app.register_blueprint(workload_bp)

    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'service': '广告公司服务监测系统后端',
            'version': '1.0.0',
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'endpoints': {
                'health': '/api/health',
                'employees': '/api/v1/employees',
                'projects': '/api/v1/projects',
                'files': '/api/v1/files',
                'dashboard': '/api/v1/dashboard',
                'chatlog': '/api/v1/chatlog'
            }
        })

    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': '广告公司服务监测系统后端'
        })

    # ------------------ 文件验证相关API（保留在app.py中） ------------------

    @app.route('/api/v1/files/validate', methods=['POST'])
    def validate_filename():
        """
            验证单个文件名是否符合规范
            请求体: JSON格式，包含 filename 字段
        返回: 验证结果
        """
        from file_validator import FileNameValidator
            
        try:
            data = request.get_json()
            if not data or 'filename' not in data:
                return jsonify({'success': False, 'error': '缺少文件名参数'}), 400
            
            filename = data['filename']
            validator = FileNameValidator()
            result = validator.validate_filename(filename)
            
            return jsonify({
                'success': True,
                'data': {
                    'filename': filename,
                    'is_valid': result['is_valid'],
                    'parsed_data': result['parsed_data'],
                    'errors': result['errors']
                }
            })
        except Exception as e:
            logger.error(f"文件名验证失败: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/v1/files/validate-batch', methods=['POST'])
    def validate_filenames_batch():
        """
            批量验证文件名
            请求体: JSON格式，包含 filenames 数组
        返回: 批量验证结果
        """
        from file_validator import FileNameValidator
            
        try:
            data = request.get_json()
            if not data or 'filenames' not in data:
                return jsonify({'success': False, 'error': '缺少文件名列表参数'}), 400
            
            filenames = data['filenames']
            if not isinstance(filenames, list):
                return jsonify({'success': False, 'error': 'filenames必须是数组'}), 400
            
            validator = FileNameValidator()
            results = []
            
            for filename in filenames:
                result = validator.validate_filename(filename)
                results.append({
                    'filename': filename,
                    'is_valid': result['is_valid'],
                    'parsed_data': result['parsed_data'],
                    'errors': result['errors']
                })
            
            return jsonify({
                'success': True,
                'data': results
            })
        except Exception as e:
            logger.error(f"批量文件名验证失败: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/v1/files/upload', methods=['POST'])
    def upload_and_validate_file():
        """
            上传并验证文件
            请求体: multipart/form-data，包含文件和其他元数据
        返回: 上传和验证结果
        """
        from file_validator import FileNameValidator
        from werkzeug.utils import secure_filename
        import os
            
        try:
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': '没有文件被上传'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': '没有选择文件'}), 400
            
            # 验证文件名
            validator = FileNameValidator()
            validation_result = validator.validate_filename(file.filename)
            
            if not validation_result['is_valid']:
                return jsonify({
                    'success': False,
                    'error': '文件名不符合规范',
                    'validation_errors': validation_result['errors']
                }), 400
                
            # 保存文件（这里简化处理，实际应该保存到指定目录）
            filename = secure_filename(file.filename)
            # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # 创建文件记录
            parsed_data = validation_result['parsed_data']
            file_record = FileRecord(
                original_name=file.filename,
                standardized_name=file.filename,
                project_name=parsed_data.get('project_name', ''),
                work_order=parsed_data.get('work_order_name', ''),
                workload=parsed_data.get('workload', ''),
                author_abbreviation=parsed_data.get('author_abbreviation', ''),
                version=parsed_data.get('version', ''),
                file_extension=parsed_data.get('extension', ''),
                upload_time=datetime.utcnow(),
                uploader=request.form.get('uploader', 'unknown'),
                file_size=str(len(file.read())),
                status='validated'
            )
            
            db.session.add(file_record)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'data': {
                    'file_id': file_record.id,
                    'filename': file.filename,
                    'validation_result': validation_result,
                    'message': '文件上传并验证成功'
                }
            })
        except Exception as e:
            logger.error(f"文件上传验证失败: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    # 全局的OPTIONS预检请求处理已由`flask_cors`扩展自动完成，不再需要手动编写兜底路由。
    # 手动编写的路由与扩展冲突，是导致CORS预检失败和"Failed to fetch"错误的根源。
    
    return app

app = create_app()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        try:
            db.create_all()
            logger.info("数据库表结构已初始化（PostgreSQL）")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
    app.run(host='0.0.0.0', port=5000, debug=True)