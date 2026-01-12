"""Add authentication fields to users

Revision ID: 5c522b5a0003
Revises: 47578bf954a5
Create Date: 2026-01-12 20:38:07.098418

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c522b5a0003'
down_revision: Union[str, Sequence[str], None] = '47578bf954a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns
    op.add_column('users', sa.Column('full_name', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('hashed_password', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean, nullable=True, default=True))
    
    # Update existing data - copy display_name to full_name
    op.execute("UPDATE users SET full_name = display_name WHERE display_name IS NOT NULL")
    op.execute("UPDATE users SET hashed_password = 'temp_hash' WHERE hashed_password IS NULL")
    op.execute("UPDATE users SET is_active = true WHERE is_active IS NULL")
    
    # Make email and new fields NOT NULL after data migration
    op.alter_column('users', 'email', nullable=False)
    op.alter_column('users', 'full_name', nullable=False)
    op.alter_column('users', 'hashed_password', nullable=False)
    op.alter_column('users', 'is_active', nullable=False)
    
    # Drop old column
    op.drop_column('users', 'display_name')


def downgrade() -> None:
    """Downgrade schema."""
    # Add back old column
    op.add_column('users', sa.Column('display_name', sa.String(255), nullable=True))
    
    # Copy data back
    op.execute("UPDATE users SET display_name = full_name WHERE full_name IS NOT NULL")
    op.alter_column('users', 'display_name', nullable=False)
    
    # Make email nullable again
    op.alter_column('users', 'email', nullable=True)
    
    # Drop new columns
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'hashed_password')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'full_name')
