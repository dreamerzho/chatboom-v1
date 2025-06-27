# 关键词管理相关API路由
# 支持关键词分类管理、关键词CRUD、关键词分析等功能

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
import json
from typing import Dict, List, Any

from models.keyword import KeywordCategory, Keyword, KeywordAnalysis, MessageKeyword
from models.chat import ChatMessage
from models.employee import EmployeeMapping
from models.project import Project
from keyword_analyzer import KeywordAnalyzer
from backend.db import db

# 创建蓝图
keywords_bp = Blueprint('keywords', __name__, url_prefix='/api/v1/keywords')
logger = logging.getLogger(__name__)

# 初始化关键词分析器
keyword_analyzer = KeywordAnalyzer()

@keywords_bp.route('/categories', methods=['GET'])
def get_keyword_categories():
    """
    获取关键词分类列表
    
    返回:
        关键词分类列表
    """
    try:
        categories = KeywordCategory.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'data': [category.to_dict() for category in categories]
        })
    except Exception as e:
        logger.error(f"获取关键词分类失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@keywords_bp.route('/categories', methods=['POST'])
def create_keyword_category():
    """
    创建关键词分类
    
    请求体:
        name: 分类名称
        description: 分类描述
        color: 分类颜色
    
    返回:
        创建结果
    """
    try:
        data = request.get_json()
        
        # 验证必填参数
        if not data or 'name' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必填参数: name'
            }), 400
        
        name = data['name']
        description = data.get('description', '')
        color = data.get('color', '#666666')
        
        # 检查分类名是否已存在
        existing = KeywordCategory.query.filter_by(name=name).first()
        if existing:
            return jsonify({
                'success': False,
                'error': f'分类名 "{name}" 已存在'
            }), 400
        
        # 创建新分类
        category = KeywordCategory(
            name=name,
            description=description,
            color=color
        )
        
        db.session.add(category)
        db.session.commit()
        
        # 刷新分析器缓存
        keyword_analyzer.refresh_keywords_cache()
        
        return jsonify({
            'success': True,
            'message': f'关键词分类 "{name}" 创建成功',
            'data': category.to_dict()
        })
        
    except Exception as e:
        logger.error(f"创建关键词分类失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@keywords_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_keyword_category(category_id: int):
    """
    更新关键词分类
    
    路径参数:
        category_id: 分类ID
    
    请求体:
        name: 分类名称
        description: 分类描述
        color: 分类颜色
        is_active: 是否启用
    
    返回:
        更新结果
    """
    try:
        category = KeywordCategory.query.get(category_id)
        if not category:
            return jsonify({
                'success': False,
                'error': f'分类ID {category_id} 不存在'
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400
        
        # 更新字段
        if 'name' in data:
            # 检查名称是否与其他分类重复
            existing = KeywordCategory.query.filter(
                KeywordCategory.name == data['name'],
                KeywordCategory.id != category_id
            ).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': f'分类名 "{data["name"]}" 已存在'
                }), 400
            category.name = data['name']
        
        if 'description' in data:
            category.description = data['description']
        
        if 'color' in data:
            category.color = data['color']
        
        if 'is_active' in data:
            category.is_active = data['is_active']
        
        category.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 刷新分析器缓存
        keyword_analyzer.refresh_keywords_cache()
        
        return jsonify({
            'success': True,
            'message': f'关键词分类更新成功',
            'data': category.to_dict()
        })
        
    except Exception as e:
        logger.error(f"更新关键词分类失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@keywords_bp.route('/keywords', methods=['GET'])
def get_keywords():
    """
    获取关键词列表
    
    查询参数:
        category_id: 分类ID（可选）
        keyword: 关键词搜索（可选）
        is_active: 是否启用（可选）
    
    返回:
        关键词列表
    """
    try:
        category_id = request.args.get('category_id', type=int)
        keyword_search = request.args.get('keyword', '')
        is_active = request.args.get('is_active', type=bool)
        
        query = Keyword.query
        
        if category_id:
            query = query.filter(Keyword.category_id == category_id)
        
        if keyword_search:
            query = query.filter(Keyword.keyword.contains(keyword_search))
        
        if is_active is not None:
            query = query.filter(Keyword.is_active == is_active)
        
        keywords = query.order_by(Keyword.keyword).all()
        
        return jsonify({
            'success': True,
            'data': [keyword.to_dict() for keyword in keywords]
        })
        
    except Exception as e:
        logger.error(f"获取关键词列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@keywords_bp.route('/keywords', methods=['POST'])
def create_keyword():
    """
    创建关键词
    
    请求体:
        keyword: 关键词内容
        category_id: 分类ID
        weight: 权重
        synonyms: 同义词列表
    
    返回:
        创建结果
    """
    try:
        data = request.get_json()
        
        # 验证必填参数
        required_fields = ['keyword', 'category_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必填参数: {field}'
                }), 400
        
        keyword_text = data['keyword']
        category_id = data['category_id']
        weight = data.get('weight', 1.0)
        synonyms = data.get('synonyms', [])
        
        # 验证分类是否存在
        category = KeywordCategory.query.get(category_id)
        if not category:
            return jsonify({
                'success': False,
                'error': f'分类ID {category_id} 不存在'
            }), 400
        
        # 检查关键词是否已存在
        existing = Keyword.query.filter_by(keyword=keyword_text).first()
        if existing:
            return jsonify({
                'success': False,
                'error': f'关键词 "{keyword_text}" 已存在'
            }), 400
        
        # 创建新关键词
        keyword = Keyword(
            keyword=keyword_text,
            category_id=category_id,
            weight=weight,
            synonyms=json.dumps(synonyms, ensure_ascii=False) if synonyms else None
        )
        
        db.session.add(keyword)
        db.session.commit()
        
        # 刷新分析器缓存
        keyword_analyzer.refresh_keywords_cache()
        
        return jsonify({
            'success': True,
            'message': f'关键词 "{keyword_text}" 创建成功',
            'data': keyword.to_dict()
        })
        
    except Exception as e:
        logger.error(f"创建关键词失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@keywords_bp.route('/keywords/<int:keyword_id>', methods=['PUT'])
def update_keyword(keyword_id: int):
    """
    更新关键词
    
    路径参数:
        keyword_id: 关键词ID
    
    请求体:
        keyword: 关键词内容
        category_id: 分类ID
        weight: 权重
        synonyms: 同义词列表
        is_active: 是否启用
    
    返回:
        更新结果
    """
    try:
        keyword = Keyword.query.get(keyword_id)
        if not keyword:
            return jsonify({
                'success': False,
                'error': f'关键词ID {keyword_id} 不存在'
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空'
            }), 400
        
        # 更新字段
        if 'keyword' in data:
            # 检查关键词是否与其他关键词重复
            existing = Keyword.query.filter(
                Keyword.keyword == data['keyword'],
                Keyword.id != keyword_id
            ).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': f'关键词 "{data["keyword"]}" 已存在'
                }), 400
            keyword.keyword = data['keyword']
        
        if 'category_id' in data:
            # 验证分类是否存在
            category = KeywordCategory.query.get(data['category_id'])
            if not category:
                return jsonify({
                    'success': False,
                    'error': f'分类ID {data["category_id"]} 不存在'
                }), 400
            keyword.category_id = data['category_id']
        
        if 'weight' in data:
            keyword.weight = data['weight']
        
        if 'synonyms' in data:
            keyword.synonyms = json.dumps(data['synonyms'], ensure_ascii=False) if data['synonyms'] else None
        
        if 'is_active' in data:
            keyword.is_active = data['is_active']
        
        keyword.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 刷新分析器缓存
        keyword_analyzer.refresh_keywords_cache()
        
        return jsonify({
            'success': True,
            'message': f'关键词更新成功',
            'data': keyword.to_dict()
        })
        
    except Exception as e:
        logger.error(f"更新关键词失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@keywords_bp.route('/analyze', methods=['POST'])
def analyze_text():
    """
    分析文本的关键词和情感
    
    请求体:
        text: 待分析文本
        project_id: 项目ID（可选）
        employee_id: 员工ID（可选）
        chatroom_name: 群聊名称（可选）
    
    返回:
        分析结果
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必填参数: text'
            }), 400
        
        text = data['text']
        project_id = data.get('project_id')
        employee_id = data.get('employee_id')
        chatroom_name = data.get('chatroom_name')
        
        # 情感分析
        sentiment_result = keyword_analyzer.analyze_sentiment(text)
        
        # 关键词提取
        extracted_keywords = keyword_analyzer.extract_keywords(text, top_k=10)
        
        return jsonify({
            'success': True,
            'data': {
                'text': text,
                'sentiment': sentiment_result,
                'keywords': extracted_keywords,
                'project_id': project_id,
                'employee_id': employee_id,
                'chatroom_name': chatroom_name
            }
        })
        
    except Exception as e:
        logger.error(f"文本分析失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@keywords_bp.route('/analyze/messages', methods=['POST'])
def analyze_messages():
    """
    批量分析消息的关键词和情感
    
    请求体:
        messages: 消息列表
        project_id: 项目ID（可选）
        employee_id: 员工ID（可选）
        chatroom_name: 群聊名称（可选）
    
    返回:
        分析结果
    """
    try:
        data = request.get_json()
        
        if not data or 'messages' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必填参数: messages'
            }), 400
        
        messages = data['messages']
        project_id = data.get('project_id')
        employee_id = data.get('employee_id')
        chatroom_name = data.get('chatroom_name')
        
        if not isinstance(messages, list):
            return jsonify({
                'success': False,
                'error': 'messages 必须是数组'
            }), 400
        
        # 批量分析
        result = keyword_analyzer.analyze_messages(
            messages=messages,
            project_id=project_id,
            employee_id=employee_id,
            chatroom_name=chatroom_name
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"批量分析消息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@keywords_bp.route('/analysis/history', methods=['GET'])
def get_analysis_history():
    """
    获取分析历史
    
    查询参数:
        project_id: 项目ID（可选）
        employee_id: 员工ID（可选）
        days: 查询天数（可选，默认30天）
    
    返回:
        分析历史列表
    """
    try:
        project_id = request.args.get('project_id', type=int)
        employee_id = request.args.get('employee_id', type=int)
        days = request.args.get('days', 30, type=int)
        
        analyses = keyword_analyzer.get_analysis_history(
            project_id=project_id,
            employee_id=employee_id,
            days=days
        )
        
        return jsonify({
            'success': True,
            'data': analyses
        })
        
    except Exception as e:
        logger.error(f"获取分析历史失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@keywords_bp.route('/analysis/trend', methods=['GET'])
def get_trend_analysis():
    """
    获取趋势分析
    
    查询参数:
        project_id: 项目ID（可选）
        employee_id: 员工ID（可选）
        days: 查询天数（可选，默认30天）
    
    返回:
        趋势分析结果
    """
    try:
        project_id = request.args.get('project_id', type=int)
        employee_id = request.args.get('employee_id', type=int)
        days = request.args.get('days', 30, type=int)
        
        result = keyword_analyzer.get_trend_analysis(
            project_id=project_id,
            employee_id=employee_id,
            days=days
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
        
    except Exception as e:
        logger.error(f"获取趋势分析失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@keywords_bp.route('/init-default', methods=['POST'])
def init_default_keywords():
    """
    初始化默认关键词库
    
    返回:
        初始化结果
    """
    try:
        # 创建默认分类
        default_categories = [
            {'name': '正面', 'description': '正面情感关键词', 'color': '#52c41a'},
            {'name': '负面', 'description': '负面情感关键词', 'color': '#ff4d4f'},
            {'name': '中性', 'description': '中性关键词', 'color': '#666666'}
        ]
        
        category_map = {}
        for cat_data in default_categories:
            existing = KeywordCategory.query.filter_by(name=cat_data['name']).first()
            if not existing:
                category = KeywordCategory(**cat_data)
                db.session.add(category)
                db.session.flush()  # 获取ID
                category_map[cat_data['name']] = category.id
            else:
                category_map[cat_data['name']] = existing.id
        
        # 创建默认关键词
        default_keywords = {
            '正面': [
                '好的', '收到', '没问题', '可以', '行', 'OK', 'ok', '完美', '优秀', '棒',
                '满意', '同意', '确认', '通过', '完成', '成功', '顺利', '高效', '专业'
            ],
            '负面': [
                '不行', '做不了', '有问题', '困难', '麻烦', '不行', '拒绝', '失败',
                '延迟', '错误', '问题', '不满', '投诉', '抱怨', '失望', '焦虑'
            ],
            '中性': [
                '项目', '设计', '文案', '视频', '海报', 'PPT', '客户', '需求',
                '修改', '调整', '确认', '反馈', '会议', '讨论', '计划', '进度'
            ]
        }
        
        created_count = 0
        for category_name, keywords in default_keywords.items():
            category_id = category_map.get(category_name)
            if not category_id:
                continue
            
            for keyword_text in keywords:
                existing = Keyword.query.filter_by(keyword=keyword_text).first()
                if not existing:
                    keyword = Keyword(
                        keyword=keyword_text,
                        category_id=category_id,
                        weight=1.0
                    )
                    db.session.add(keyword)
                    created_count += 1
        
        db.session.commit()
        
        # 刷新分析器缓存
        keyword_analyzer.refresh_keywords_cache()
        
        return jsonify({
            'success': True,
            'message': f'默认关键词库初始化成功，创建了 {created_count} 个关键词',
            'data': {
                'categories_created': len(default_categories),
                'keywords_created': created_count
            }
        })
        
    except Exception as e:
        logger.error(f"初始化默认关键词库失败: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500 