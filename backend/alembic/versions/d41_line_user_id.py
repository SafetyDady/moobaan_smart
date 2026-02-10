"""Phase D.4.1: Add line_user_id to users

Revision ID: d41_line_user_id
Revises: g2_export_audit_log
Create Date: 2026-02-10

Purpose:
- Add line_user_id column for LINE Login authentication
- Unique index for fast lookup by LINE user ID
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd41_line_user_id'
down_revision = 'd2_session_version'
branch_labels = None
depends_on = None


def upgrade():
    # Add line_user_id column
    op.add_column('users', sa.Column('line_user_id', sa.String(100), nullable=True))
    
    # Create unique index for LINE user lookup
    op.create_index('ix_users_line_user_id', 'users', ['line_user_id'], unique=True)


def downgrade():
    op.drop_index('ix_users_line_user_id', table_name='users')
    op.drop_column('users', 'line_user_id')
