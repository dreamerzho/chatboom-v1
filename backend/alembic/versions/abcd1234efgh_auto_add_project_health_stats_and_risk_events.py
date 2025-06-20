"""
Alembic 自动迁移脚本：新增 project_health_stats 和 risk_events 两个核心表
"""

# Alembic 版本标识
revision = 'abcd1234efgh'
down_revision = 'e0ec0404bf4e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    # 新建 project_health_stats 表
    op.create_table(
        'project_health_stats',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('period', sa.String(length=16), nullable=False),
        sa.Column('health_score', sa.Integer(), nullable=False),
        sa.Column('avg_time_to_final', sa.Float()),
        sa.Column('avg_revisions', sa.Float()),
        sa.Column('risk_count', sa.Integer(), server_default='0'),
        sa.Column('warning_count', sa.Integer(), server_default='0'),
        sa.Column('negative_sentiment_rate', sa.Float()),
        sa.Column('created_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'])
    )
    # 新建 risk_events 表
    op.create_table(
        'risk_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer()),
        sa.Column('event_type', sa.String(length=32), nullable=False),
        sa.Column('event_desc', sa.String(length=256)),
        sa.Column('event_time', sa.DateTime()),
        sa.Column('severity', sa.String(length=8), server_default='中'),
        sa.Column('resolved', sa.Boolean(), server_default=sa.sql.expression.false()),
        sa.Column('attribution', sa.String(length=32)),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['employee_id'], ['employee_mappings.id'])
    )

def downgrade():
    op.drop_table('risk_events')
    op.drop_table('project_health_stats') 