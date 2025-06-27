#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版去重功能测试脚本
验证基于 seq 字段的高效去重机制
"""

import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import db
from models.chat import ChatMessage
from models.file import FileRecord
from models.project import Project
from sqlalchemy.dialects.postgresql import insert

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_message_deduplication():
    """测试消息去重功能"""
    logger.info("=== 开始测试消息去重功能 ===")
    
    try:
        # 创建测试项目
        test_project = Project(
            project_name="测试去重项目",
            description="用于测试去重功能的项目",
            status="active"
        )
        db.session.add(test_project)
        db.session.commit()
        project_id = test_project.id
        logger.info(f"创建测试项目，ID: {project_id}")
        
        # 准备测试数据 - 包含重复的 message_id
        test_messages = [
            {
                'message_id': '1234567890123',
                'project_id': project_id,
                'talker_name': '测试群聊',
                'sender_name': '用户A',
                'message_type': '文本',
                'content': '第一条消息',
                'timestamp': datetime.now(),
                'created_at': datetime.now()
            },
            {
                'message_id': '1234567890123',  # 重复的 message_id
                'project_id': project_id,
                'talker_name': '测试群聊',
                'sender_name': '用户A',
                'message_type': '文本',
                'content': '重复的第一条消息',
                'timestamp': datetime.now(),
                'created_at': datetime.now()
            },
            {
                'message_id': '1234567890124',
                'project_id': project_id,
                'talker_name': '测试群聊',
                'sender_name': '用户B',
                'message_type': '文本',
                'content': '第二条消息',
                'timestamp': datetime.now(),
                'created_at': datetime.now()
            }
        ]
        
        # 第一次批量插入
        logger.info("第一次批量插入消息...")
        insert_stmt = insert(ChatMessage).values(test_messages)
        do_nothing_stmt = insert_stmt.on_conflict_do_nothing(
            index_elements=['project_id', 'message_id']
        )
        result1 = db.session.execute(do_nothing_stmt)
        db.session.commit()
        inserted_count1 = result1.rowcount if hasattr(result1, 'rowcount') else len(test_messages)
        logger.info(f"第一次插入结果：成功 {inserted_count1} 条")
        
        # 第二次批量插入相同数据
        logger.info("第二次批量插入相同消息...")
        result2 = db.session.execute(do_nothing_stmt)
        db.session.commit()
        inserted_count2 = result2.rowcount if hasattr(result2, 'rowcount') else 0
        logger.info(f"第二次插入结果：成功 {inserted_count2} 条")
        
        # 验证数据库中的实际记录数
        actual_count = ChatMessage.query.filter_by(project_id=project_id).count()
        logger.info(f"数据库中实际记录数：{actual_count}")
        
        # 验证去重是否成功
        if inserted_count1 == 3 and inserted_count2 == 0 and actual_count == 3:
            logger.info("✅ 消息去重测试通过！")
            return True
        else:
            logger.error("❌ 消息去重测试失败！")
            return False
            
    except Exception as e:
        logger.error(f"消息去重测试异常: {e}")
        return False
    finally:
        # 清理测试数据
        try:
            ChatMessage.query.filter_by(project_id=project_id).delete()
            Project.query.filter_by(id=project_id).delete()
            db.session.commit()
            logger.info("测试数据清理完成")
        except Exception as e:
            logger.error(f"清理测试数据失败: {e}")

def test_file_deduplication():
    """测试文件去重功能"""
    logger.info("=== 开始测试文件去重功能 ===")
    
    try:
        # 准备测试数据 - 包含重复的 message_seq + original_name
        test_files = [
            {
                'message_seq': '1234567890123',
                'original_name': 'test_file.pdf',
                'standardized_name': 'test_file.pdf',
                'project_name': '测试项目',
                'author_abbreviation': 'TEST',
                'file_extension': 'pdf',
                'upload_time': datetime.now(),
                'uploader': '测试用户',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            },
            {
                'message_seq': '1234567890123',  # 重复的 message_seq
                'original_name': 'test_file.pdf',  # 重复的文件名
                'standardized_name': 'test_file.pdf',
                'project_name': '测试项目',
                'author_abbreviation': 'TEST',
                'file_extension': 'pdf',
                'upload_time': datetime.now(),
                'uploader': '测试用户',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            },
            {
                'message_seq': '1234567890124',
                'original_name': 'another_file.pdf',
                'standardized_name': 'another_file.pdf',
                'project_name': '测试项目',
                'author_abbreviation': 'TEST',
                'file_extension': 'pdf',
                'upload_time': datetime.now(),
                'uploader': '测试用户',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        ]
        
        # 第一次批量插入
        logger.info("第一次批量插入文件...")
        insert_stmt = insert(FileRecord).values(test_files)
        do_nothing_stmt = insert_stmt.on_conflict_do_nothing(
            index_elements=['message_seq', 'original_name']
        )
        result1 = db.session.execute(do_nothing_stmt)
        db.session.commit()
        inserted_count1 = result1.rowcount if hasattr(result1, 'rowcount') else len(test_files)
        logger.info(f"第一次插入结果：成功 {inserted_count1} 条")
        
        # 第二次批量插入相同数据
        logger.info("第二次批量插入相同文件...")
        result2 = db.session.execute(do_nothing_stmt)
        db.session.commit()
        inserted_count2 = result2.rowcount if hasattr(result2, 'rowcount') else 0
        logger.info(f"第二次插入结果：成功 {inserted_count2} 条")
        
        # 验证数据库中的实际记录数
        actual_count = FileRecord.query.filter_by(project_name='测试项目').count()
        logger.info(f"数据库中实际记录数：{actual_count}")
        
        # 验证去重是否成功 - 期望：第一次插入3条（其中1条重复被跳过），第二次插入0条
        expected_first_insert = 2  # 3条数据中，2条是唯一的
        if inserted_count1 == expected_first_insert and inserted_count2 == 0 and actual_count == expected_first_insert:
            logger.info("✅ 文件去重测试通过！")
            return True
        else:
            logger.error(f"❌ 文件去重测试失败！期望第一次插入{expected_first_insert}条，实际{inserted_count1}条")
            return False
            
    except Exception as e:
        logger.error(f"文件去重测试异常: {e}")
        return False
    finally:
        # 清理测试数据
        try:
            FileRecord.query.filter_by(project_name='测试项目').delete()
            logger.info("测试数据清理完成")
        except Exception as e:
            logger.error(f"清理测试数据失败: {e}")

def main():
    """主测试函数"""
    logger.info("开始执行简化版去重功能测试...")
    
    # 初始化数据库连接
    try:
        # 直接使用数据库连接，避免 Flask app context 问题
        from config import Config
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # 创建数据库引擎
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        db.session = Session()
        
        # 执行各项测试
        test_results = []
        
        test_results.append(("消息去重", test_message_deduplication()))
        test_results.append(("文件去重", test_file_deduplication()))
        
        # 输出测试结果
        logger.info("\n=== 测试结果汇总 ===")
        all_passed = True
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"{test_name}: {status}")
            if not result:
                all_passed = False
        
        if all_passed:
            logger.info("🎉 所有去重功能测试通过！")
        else:
            logger.error("💥 部分去重功能测试失败！")
            
    except Exception as e:
        logger.error(f"测试执行异常: {e}")

if __name__ == "__main__":
    main() 