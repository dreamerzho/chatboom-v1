#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行去重约束数据库迁移脚本
添加基于 seq 字段的复合唯一约束
"""

import sys
import os
import logging
from sqlalchemy import text

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import db
from app import app

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_deduplication_constraints():
    """应用去重约束"""
    logger.info("开始应用去重约束...")
    
    try:
        with app.app_context():
            # 检查约束是否已存在
            def constraint_exists(table_name, constraint_name):
                """检查约束是否已存在"""
                sql = """
                SELECT COUNT(*) 
                FROM information_schema.table_constraints 
                WHERE table_name = :table_name 
                AND constraint_name = :constraint_name
                """
                result = db.session.execute(text(sql), {
                    'table_name': table_name,
                    'constraint_name': constraint_name
                }).scalar()
                return result > 0
            
            # 为 chat_messages 表添加复合唯一约束
            if not constraint_exists('chat_messages', 'uq_project_message'):
                logger.info("为 chat_messages 表添加复合唯一约束...")
                sql = """
                ALTER TABLE chat_messages 
                ADD CONSTRAINT uq_project_message 
                UNIQUE (project_id, message_id)
                """
                db.session.execute(text(sql))
                logger.info("✅ chat_messages 表约束添加成功")
            else:
                logger.info("chat_messages 表约束已存在，跳过")
            
            # 为 file_records 表添加复合唯一约束
            if not constraint_exists('file_records', 'uq_message_file'):
                logger.info("为 file_records 表添加复合唯一约束...")
                sql = """
                ALTER TABLE file_records 
                ADD CONSTRAINT uq_message_file 
                UNIQUE (message_seq, original_name)
                """
                db.session.execute(text(sql))
                logger.info("✅ file_records 表约束添加成功")
            else:
                logger.info("file_records 表约束已存在，跳过")
            
            # 提交事务
            db.session.commit()
            logger.info("🎉 所有去重约束应用成功！")
            
            # 验证约束
            verify_constraints()
            
    except Exception as e:
        logger.error(f"应用去重约束失败: {e}")
        db.session.rollback()
        raise

def verify_constraints():
    """验证约束是否正确应用"""
    logger.info("验证去重约束...")
    
    try:
        # 检查 chat_messages 表约束
        sql = """
        SELECT constraint_name, constraint_type 
        FROM information_schema.table_constraints 
        WHERE table_name = 'chat_messages' 
        AND constraint_name = 'uq_project_message'
        """
        result = db.session.execute(text(sql)).fetchone()
        if result:
            logger.info(f"✅ chat_messages 约束验证成功: {result[0]} ({result[1]})")
        else:
            logger.error("❌ chat_messages 约束验证失败")
        
        # 检查 file_records 表约束
        sql = """
        SELECT constraint_name, constraint_type 
        FROM information_schema.table_constraints 
        WHERE table_name = 'file_records' 
        AND constraint_name = 'uq_message_file'
        """
        result = db.session.execute(text(sql)).fetchone()
        if result:
            logger.info(f"✅ file_records 约束验证成功: {result[0]} ({result[1]})")
        else:
            logger.error("❌ file_records 约束验证失败")
            
    except Exception as e:
        logger.error(f"验证约束失败: {e}")

def test_constraints():
    """测试约束是否正常工作"""
    logger.info("测试约束功能...")
    
    try:
        from models.chat import ChatMessage
        from models.file import FileRecord
        from models.project import Project
        from datetime import datetime
        
        # 创建测试项目
        test_project = Project(
            project_name="约束测试项目",
            description="用于测试约束功能",
            status="active"
        )
        db.session.add(test_project)
        db.session.commit()
        project_id = test_project.id
        
        # 测试消息约束
        try:
            # 插入第一条消息
            msg1 = ChatMessage(
                message_id='test_seq_123',
                project_id=project_id,
                talker_name='测试群',
                sender_name='用户A',
                message_type='文本',
                content='测试消息',
                timestamp=datetime.now()
            )
            db.session.add(msg1)
            db.session.commit()
            logger.info("✅ 第一条消息插入成功")
            
            # 尝试插入重复消息（应该失败）
            msg2 = ChatMessage(
                message_id='test_seq_123',  # 相同的 seq
                project_id=project_id,      # 相同的项目
                talker_name='测试群',
                sender_name='用户A',
                message_type='文本',
                content='重复消息',
                timestamp=datetime.now()
            )
            db.session.add(msg2)
            db.session.commit()
            logger.error("❌ 重复消息插入成功，约束可能无效")
            
        except Exception as e:
            logger.info(f"✅ 重复消息被正确阻止: {str(e)[:100]}")
            db.session.rollback()
        
        # 测试文件约束
        try:
            # 插入第一个文件
            file1 = FileRecord(
                message_seq='test_seq_123',
                original_name='test.pdf',
                standardized_name='test.pdf',
                project_name='测试项目',
                author_abbreviation='TEST',
                file_extension='pdf',
                upload_time=datetime.now(),
                uploader='测试用户'
            )
            db.session.add(file1)
            db.session.commit()
            logger.info("✅ 第一个文件插入成功")
            
            # 尝试插入重复文件（应该失败）
            file2 = FileRecord(
                message_seq='test_seq_123',  # 相同的 seq
                original_name='test.pdf',    # 相同的文件名
                standardized_name='test.pdf',
                project_name='测试项目',
                author_abbreviation='TEST',
                file_extension='pdf',
                upload_time=datetime.now(),
                uploader='测试用户'
            )
            db.session.add(file2)
            db.session.commit()
            logger.error("❌ 重复文件插入成功，约束可能无效")
            
        except Exception as e:
            logger.info(f"✅ 重复文件被正确阻止: {str(e)[:100]}")
            db.session.rollback()
        
        # 清理测试数据
        ChatMessage.query.filter_by(project_id=project_id).delete()
        FileRecord.query.filter_by(project_name='测试项目').delete()
        Project.query.filter_by(id=project_id).delete()
        db.session.commit()
        logger.info("测试数据清理完成")
        
    except Exception as e:
        logger.error(f"测试约束功能失败: {e}")
        db.session.rollback()

def main():
    """主函数"""
    logger.info("开始执行去重约束迁移...")
    
    try:
        # 应用约束
        apply_deduplication_constraints()
        
        # 测试约束
        test_constraints()
        
        logger.info("🎉 去重约束迁移完成！")
        
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 