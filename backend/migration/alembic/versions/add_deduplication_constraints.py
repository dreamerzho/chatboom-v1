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
    # 为 chat_messages 表添加复合唯一约束
    op.create_unique_constraint(
        'uq_project_message', 
        'chat_messages', 
        ['project_id', 'message_id']
    )
    
    # 为 file_records 表添加复合唯一约束
    op.create_unique_constraint(
        'uq_message_file', 
        'file_records', 
        ['message_seq', 'original_name']
    )

def downgrade() -> None:
    """移除去重约束"""
    # 移除 chat_messages 表的复合唯一约束
    op.drop_constraint('uq_project_message', 'chat_messages', type_='unique')
    
    # 移除 file_records 表的复合唯一约束
    op.drop_constraint('uq_message_file', 'file_records', type_='unique') 