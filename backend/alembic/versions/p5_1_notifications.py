"""Phase 5.1: Create notifications table

Revision ID: p5_1_notifications
Revises: (auto)
Create Date: 2026-02-25
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'p5_1_notifications'
down_revision = None  # Will be set during migration chain
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('reference_type', sa.String(50), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('is_read', sa.Boolean(), default=False, nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    # Indexes for performance
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_type', 'notifications', ['type'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    # Composite index for common query: user's unread notifications
    op.create_index('ix_notifications_user_unread', 'notifications', ['user_id', 'is_read', 'is_deleted'])


def downgrade():
    op.drop_index('ix_notifications_user_unread')
    op.drop_index('ix_notifications_created_at')
    op.drop_index('ix_notifications_is_read')
    op.drop_index('ix_notifications_type')
    op.drop_index('ix_notifications_user_id')
    op.drop_table('notifications')
