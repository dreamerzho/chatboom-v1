"""添加去重约束

Revision ID: add_deduplication_constraints
Revises: 064d768677b9
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_deduplication_constraints'
down_revision = '064d768677b9'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """添加去重约束"""
    # chat_messages 表：删除自动生成和历史唯一约束，添加复合唯一约束
    with op.batch_alter_table('chat_messages') as batch_op:
        for cname in ['chat_messages_message_id_key', 'uq_project_message']:
            try:
                batch_op.drop_constraint(cname, type_='unique')
            except Exception:
                pass
        batch_op.create_unique_constraint('uq_project_message', ['project_id', 'message_id'])
    
    # file_records 表：只删除实际存在的 uq_message_file 约束，添加复合唯一约束
    with op.batch_alter_table('file_records') as batch_op:
        try:
            batch_op.drop_constraint('uq_message_file', type_='unique')
        except Exception:
            pass
        batch_op.create_unique_constraint('uq_project_chatroom_filename', ['project_id', 'chatroom_name', 'original_name'])

def downgrade() -> None:
    """移除去重约束"""
    # chat_messages 表：移除复合唯一约束，恢复 message_id 唯一约束
    with op.batch_alter_table('chat_messages') as batch_op:
        batch_op.drop_constraint('uq_project_message', type_='unique')
        batch_op.create_unique_constraint('chat_messages_message_id_key', ['message_id'])
    
    # file_records 表：移除复合唯一约束，恢复 message_seq+original_name 唯一约束
    with op.batch_alter_table('file_records') as batch_op:
        batch_op.drop_constraint('uq_project_chatroom_filename', type_='unique')
        batch_op.create_unique_constraint('uq_message_file', ['message_seq', 'original_name']) 