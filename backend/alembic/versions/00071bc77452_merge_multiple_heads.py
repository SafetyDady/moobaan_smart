"""merge_multiple_heads

Revision ID: 00071bc77452
Revises: g1_period_snapshots, r3_resident_house_audit
Create Date: 2026-01-27 00:07:21.992820

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00071bc77452'
down_revision: Union[str, Sequence[str], None] = ('g1_period_snapshots', 'r3_resident_house_audit')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
