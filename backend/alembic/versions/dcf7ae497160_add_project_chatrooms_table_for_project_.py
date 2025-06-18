"""add project_chatrooms table for project-chatroom many-to-many

Revision ID: dcf7ae497160
Revises: 51372f06c1e6
Create Date: 2025-06-17 14:04:11.753543

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'dcf7ae497160'
down_revision: Union[str, Sequence[str], None] = '51372f06c1e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """升级 schema，仅创建 project_chatrooms 多对多关联表"""
    op.create_table(
        'project_chatrooms',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('project_id', sa.Integer, sa.ForeignKey('projects.id'), nullable=False),
        sa.Column('chatroom_id', sa.String(128), nullable=False),
        sa.Column('chatroom_name', sa.String(128), nullable=False),
        sa.Column('chatroom_type', sa.String(32), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

def downgrade() -> None:
    """降级 schema，仅删除 project_chatrooms 表"""
    op.drop_table('project_chatrooms')
