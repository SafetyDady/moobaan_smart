"""
Phase R.3: Resident House Audit Log Migration

Creates the resident_house_audit_logs table.

IMPORTANT:
- Additive only - no changes to existing tables
- No cascade delete - preserve audit trail
"""

from alembic import op
import sqlalchemy as sa

revision = 'r3_resident_house_audit'
down_revision = 'r2_user_phone_auth'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'resident_house_audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('event_type', sa.String(50), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('house_id', sa.Integer(), sa.ForeignKey('houses.id'), nullable=True),
        sa.Column('from_house_id', sa.Integer(), sa.ForeignKey('houses.id'), nullable=True),
        sa.Column('to_house_id', sa.Integer(), sa.ForeignKey('houses.id'), nullable=True),
        sa.Column('house_code', sa.String(50), nullable=True),
        sa.Column('from_house_code', sa.String(50), nullable=True),
        sa.Column('to_house_code', sa.String(50), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )
    
    # Create indexes for common queries
    op.create_index('ix_resident_house_audit_user_event', 'resident_house_audit_logs', ['user_id', 'event_type'])


def downgrade():
    op.drop_index('ix_resident_house_audit_user_event', table_name='resident_house_audit_logs')
    op.drop_table('resident_house_audit_logs')
