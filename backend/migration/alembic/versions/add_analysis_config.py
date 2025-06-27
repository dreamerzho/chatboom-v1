"""add analysis_config table

Revision ID: add_analysis_config
Revises: 
Create Date: 2025-06-27

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_analysis_config'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'analysis_config',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('key', sa.String(64), unique=True, nullable=False),
        sa.Column('value', sa.String(128), nullable=False),
        sa.Column('description', sa.String(256)),
        sa.Column('updated_at', sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )

def downgrade():
    op.drop_table('analysis_config') 