"""add role to employee_mappings

Revision ID: 51372f06c1e6
Revises: 
Create Date: 2025-06-17 13:43:36.692722

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '51372f06c1e6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级 schema，仅为 employee_mappings 增加 role 字段"""
    op.add_column('employee_mappings', sa.Column('role', sa.String(length=32), nullable=False, server_default='内部员工'))


def downgrade() -> None:
    """降级 schema，仅移除 employee_mappings 的 role 字段"""
    op.drop_column('employee_mappings', 'role')
