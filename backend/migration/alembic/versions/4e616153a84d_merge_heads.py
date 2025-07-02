"""merge heads

Revision ID: 4e616153a84d
Revises: 2ddf19fcd429, add_analysis_config
Create Date: 2025-07-02 14:50:24.084636

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e616153a84d'
down_revision: Union[str, Sequence[str], None] = ('2ddf19fcd429', 'add_analysis_config')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
