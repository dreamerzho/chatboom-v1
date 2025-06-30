#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词分析器
实现关键词提取、情感分析、趋势分析等功能
支持正面/负面/中性关键词的识别和统计
"""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
import jieba
import jieba.analyse

from backend.models.keyword import KeywordCategory, Keyword, KeywordAnalysis, MessageKeyword
from backend.models.chat import ChatMessage
from backend.models.employee import EmployeeMapping
from backend.models.project import Project
from backend.db import db

logger = logging.getLogger(__name__)

class KeywordAnalyzer:
    """
    关键词分析器
    负责文本关键词提取、情感分析、趋势分析等
    """
    
    def __init__(self):
        """初始化分析器"""
        self.keywords_cache = {}  # 关键词缓存
        self.categories_cache = {}  # 分类缓存
        self._load_keywords()
        
        # 初始化jieba分词
        jieba.initialize()
        
        # 添加自定义词典
        self._add_custom_dict()
    
    def _add_custom_dict(self):
        """添加自定义词典，提高分词准确性"""
        custom_words = [
            '好的', '收到', '没问题', '可以', '行', 'OK', 'ok',
            '不行', '做不了', '有问题', '困难', '麻烦', '不行',
            '项目', '设计', '文案', '视频', '海报', 'PPT',
            '客户', '需求', '修改', '调整', '确认', '反馈'
        ]
        
        for word in custom_words:
            jieba.add_word(word)
    
    def _load_keywords(self):
        """从数据库加载关键词和分类"""
        try:
            # 加载分类
            categories = KeywordCategory.query.filter_by(is_active=True).all()
            for category in categories:
                self.categories_cache[category.id] = category
            
            # 加载关键词
            keywords = Keyword.query.filter_by(is_active=True).all()
            for keyword in keywords:
                if keyword.category_id not in self.keywords_cache:
                    self.keywords_cache[keyword.category_id] = []
                self.keywords_cache[keyword.category_id].append(keyword)
            
            logger.info(f"加载关键词完成：{len(categories)} 个分类，{len(keywords)} 个关键词")
            
        except Exception as e:
            logger.error(f"加载关键词失败: {str(e)}")
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        从文本中提取关键词
        
        参数:
            text: 待分析文本
            top_k: 返回前k个关键词
        
        返回:
            关键词列表，每个元素为(关键词, 权重)
        """
        try:
            if not text or len(text.strip()) == 0:
                return []
            
            # 使用jieba提取关键词
            keywords = jieba.analyse.extract_tags(
                text, 
                topK=top_k, 
                withWeight=True,
                allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'a', 'an')
            )
            
            return keywords
            
        except Exception as e:
            logger.error(f"关键词提取失败: {str(e)}")
            return []
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        分析文本情感倾向
        
        参数:
            text: 待分析文本
        
        返回:
            情感分析结果
        """
        try:
            if not text or len(text.strip()) == 0:
                return {
                    'positive_score': 0.0,
                    'negative_score': 0.0,
                    'neutral_score': 1.0,
                    'overall_sentiment': 'neutral',
                    'keywords_found': []
                }
            
            positive_score = 0.0
            negative_score = 0.0
            neutral_score = 0.0
            keywords_found = []
            
            # 分析每个分类的关键词
            for category_id, keywords in self.keywords_cache.items():
                category = self.categories_cache.get(category_id)
                if not category:
                    continue
                
                for keyword in keywords:
                    # 检查关键词是否在文本中
                    if keyword.keyword in text:
                        weight = keyword.weight
                        keywords_found.append({
                            'keyword': keyword.keyword,
                            'category': category.name,
                            'weight': weight
                        })
                        
                        if category.name == '正面':
                            positive_score += weight
                        elif category.name == '负面':
                            negative_score += weight
                        else:
                            neutral_score += weight
            
            # 计算总分数
            total_score = positive_score + negative_score + neutral_score
            
            if total_score > 0:
                positive_score = positive_score / total_score
                negative_score = negative_score / total_score
                neutral_score = neutral_score / total_score
            else:
                neutral_score = 1.0
            
            # 确定整体情感倾向
            if positive_score > negative_score and positive_score > neutral_score:
                overall_sentiment = 'positive'
            elif negative_score > positive_score and negative_score > neutral_score:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'
            
            return {
                'positive_score': round(positive_score, 3),
                'negative_score': round(negative_score, 3),
                'neutral_score': round(neutral_score, 3),
                'overall_sentiment': overall_sentiment,
                'keywords_found': keywords_found
            }
            
        except Exception as e:
            logger.error(f"情感分析失败: {str(e)}")
            return {
                'positive_score': 0.0,
                'negative_score': 0.0,
                'neutral_score': 1.0,
                'overall_sentiment': 'neutral',
                'keywords_found': []
            }
    
    def analyze_messages(self, 
                        messages: List[Dict[str, Any]], 
                        project_id: Optional[int] = None,
                        employee_id: Optional[int] = None,
                        chatroom_name: Optional[str] = None) -> Dict[str, Any]:
        """
        批量分析消息的关键词和情感
        
        参数:
            messages: 消息列表
            project_id: 项目ID
            employee_id: 员工ID
            chatroom_name: 群聊名称
        
        返回:
            分析结果
        """
        try:
            analysis_date = datetime.now().date()
            
            # 初始化统计
            total_messages = len(messages)
            analyzed_messages = 0
            positive_score = 0.0
            negative_score = 0.0
            neutral_score = 0.0
            
            keyword_counter = Counter()  # 关键词计数
            sentiment_scores = []  # 情感得分列表
            message_keywords = []  # 消息关键词关联
            
            # 分析每条消息
            for message in messages:
                content = message.get('content', '')
                if not content or len(content.strip()) == 0:
                    continue
                
                # 情感分析
                sentiment_result = self.analyze_sentiment(content)
                
                # 关键词提取
                extracted_keywords = self.extract_keywords(content, top_k=5)
                
                # 统计
                analyzed_messages += 1
                positive_score += sentiment_result['positive_score']
                negative_score += sentiment_result['negative_score']
                neutral_score += sentiment_result['neutral_score']
                sentiment_scores.append(sentiment_result['overall_sentiment'])
                
                # 统计关键词
                for keyword, weight in extracted_keywords:
                    keyword_counter[keyword] += weight
                
                # 记录消息关键词关联
                message_seq = message.get('seq')
                if message_seq:
                    for keyword_info in sentiment_result['keywords_found']:
                        message_keywords.append({
                            'message_seq': message_seq,
                            'keyword_text': keyword_info['keyword'],
                            'sentiment_score': keyword_info['weight']
                        })
            
            # 计算平均情感得分
            if analyzed_messages > 0:
                positive_score = positive_score / analyzed_messages
                negative_score = negative_score / analyzed_messages
                neutral_score = neutral_score / analyzed_messages
            
            # 确定整体情感倾向
            if positive_score > negative_score and positive_score > neutral_score:
                overall_sentiment = 'positive'
            elif negative_score > positive_score and negative_score > neutral_score:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'
            
            # 获取高频关键词
            top_keywords = keyword_counter.most_common(10)
            
            # 计算情感趋势
            sentiment_trend = Counter(sentiment_scores)
            
            # 保存分析结果
            analysis = KeywordAnalysis(
                analysis_date=analysis_date,
                project_id=project_id,
                employee_id=employee_id,
                chatroom_name=chatroom_name,
                total_messages=total_messages,
                analyzed_messages=analyzed_messages,
                positive_score=positive_score,
                negative_score=negative_score,
                neutral_score=neutral_score,
                overall_sentiment=overall_sentiment,
                keyword_stats=json.dumps(dict(keyword_counter), ensure_ascii=False),
                top_keywords=json.dumps(top_keywords, ensure_ascii=False),
                sentiment_trend=json.dumps(dict(sentiment_trend), ensure_ascii=False)
            )
            
            db.session.add(analysis)
            db.session.commit()
            
            # 保存消息关键词关联
            for msg_keyword in message_keywords:
                keyword_record = MessageKeyword(
                    message_seq=msg_keyword['message_seq'],
                    keyword_text=msg_keyword['keyword_text'],
                    sentiment_score=msg_keyword['sentiment_score']
                )
                db.session.add(keyword_record)
            
            db.session.commit()
            
            logger.info(f"关键词分析完成："
                       f"分析 {analyzed_messages}/{total_messages} 条消息，"
                       f"情感倾向: {overall_sentiment}，"
                       f"发现 {len(keyword_counter)} 个关键词")
            
            return {
                'success': True,
                'analysis_id': analysis.id,
                'total_messages': total_messages,
                'analyzed_messages': analyzed_messages,
                'positive_score': positive_score,
                'negative_score': negative_score,
                'neutral_score': neutral_score,
                'overall_sentiment': overall_sentiment,
                'top_keywords': top_keywords,
                'sentiment_trend': dict(sentiment_trend),
                'message_keywords_count': len(message_keywords)
            }
            
        except Exception as e:
            logger.error(f"批量分析消息失败: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_analysis_history(self, 
                           project_id: Optional[int] = None,
                           employee_id: Optional[int] = None,
                           days: int = 30) -> List[Dict[str, Any]]:
        """
        获取分析历史
        
        参数:
            project_id: 项目ID
            employee_id: 员工ID
            days: 查询天数
        
        返回:
            分析历史列表
        """
        try:
            start_date = datetime.now().date() - timedelta(days=days)
            
            query = KeywordAnalysis.query.filter(
                KeywordAnalysis.analysis_date >= start_date
            )
            
            if project_id:
                query = query.filter(KeywordAnalysis.project_id == project_id)
            
            if employee_id:
                query = query.filter(KeywordAnalysis.employee_id == employee_id)
            
            analyses = query.order_by(KeywordAnalysis.analysis_date.desc()).all()
            
            return [analysis.to_dict() for analysis in analyses]
            
        except Exception as e:
            logger.error(f"获取分析历史失败: {str(e)}")
            return []
    
    def get_trend_analysis(self, 
                          project_id: Optional[int] = None,
                          employee_id: Optional[int] = None,
                          days: int = 30) -> Dict[str, Any]:
        """
        获取趋势分析
        
        参数:
            project_id: 项目ID
            employee_id: 员工ID
            days: 查询天数
        
        返回:
            趋势分析结果
        """
        try:
            analyses = self.get_analysis_history(project_id, employee_id, days)
            
            if not analyses:
                return {
                    'success': False,
                    'error': '没有找到分析数据'
                }
            
            # 按日期分组
            daily_data = defaultdict(list)
            for analysis in analyses:
                date = analysis['analysis_date']
                daily_data[date].append(analysis)
            
            # 计算每日平均值
            trend_data = []
            for date in sorted(daily_data.keys()):
                day_analyses = daily_data[date]
                
                avg_positive = sum(a['positive_score'] for a in day_analyses) / len(day_analyses)
                avg_negative = sum(a['negative_score'] for a in day_analyses) / len(day_analyses)
                avg_neutral = sum(a['neutral_score'] for a in day_analyses) / len(day_analyses)
                
                trend_data.append({
                    'date': date,
                    'positive_score': round(avg_positive, 3),
                    'negative_score': round(avg_negative, 3),
                    'neutral_score': round(avg_neutral, 3),
                    'message_count': sum(a['total_messages'] for a in day_analyses)
                })
            
            return {
                'success': True,
                'trend_data': trend_data,
                'total_days': len(trend_data),
                'total_analyses': len(analyses)
            }
            
        except Exception as e:
            logger.error(f"趋势分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def refresh_keywords_cache(self):
        """刷新关键词缓存"""
        self.keywords_cache.clear()
        self.categories_cache.clear()
        self._load_keywords()
        logger.info("关键词缓存已刷新") 