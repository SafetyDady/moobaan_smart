"""
Phase G.2: Export Audit Log Migration

Creates the export_audit_logs table for tracking accounting exports.
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = 'g2_export_audit_log'
down_revision = None  # Will be linked to latest revision
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'export_audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('from_period', sa.String(10), nullable=False),
        sa.Column('to_period', sa.String(10), nullable=False),
        sa.Column('export_type', sa.String(50), nullable=False),
        sa.Column('reports_included', sa.Text(), nullable=False),
        sa.Column('exported_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for faster lookups
    op.create_index('ix_export_audit_logs_user_id', 'export_audit_logs', ['user_id'])
    op.create_index('ix_export_audit_logs_exported_at', 'export_audit_logs', ['exported_at'])


def downgrade():
    op.drop_index('ix_export_audit_logs_exported_at', 'export_audit_logs')
    op.drop_index('ix_export_audit_logs_user_id', 'export_audit_logs')
    op.drop_table('export_audit_logs')
