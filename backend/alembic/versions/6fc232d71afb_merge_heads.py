"""merge_heads

Revision ID: 6fc232d71afb
Revises: 6a7b8c9d0e1f, add_statement_match
Create Date: 2026-01-16 12:17:50.013674

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6fc232d71afb'
down_revision: Union[str, Sequence[str], None] = ('6a7b8c9d0e1f', 'add_statement_match')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
