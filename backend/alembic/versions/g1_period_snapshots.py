"""Phase G.1: Period Snapshots (Period Closing)

Revision ID: g1_period_snapshots
Revises: f2_chart_of_accounts
Create Date: 2026-01-20

Purpose:
- Logical soft lock for historical data
- Preserve historical truth for reporting
- Prevent accidental retroactive changes
- NO accounting mutation logic

Explicit Non-Goals:
- No journal entries
- No GL accounts
- No balance calculation
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ENUM


# revision identifiers
revision = 'g1_period_snapshots'
down_revision = 'f2_chart_of_accounts'
branch_labels = None
depends_on = None

# Create the enum type with create_type=False to use existing
period_status_enum = ENUM('DRAFT', 'LOCKED', name='period_status', create_type=False)


def upgrade():
    # Create period_status enum (if not exists)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE period_status AS ENUM ('DRAFT', 'LOCKED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create period_snapshots table
    op.create_table(
        'period_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('period_year', sa.Integer(), nullable=False),
        sa.Column('period_month', sa.Integer(), nullable=False),
        sa.Column('as_of_date', sa.Date(), nullable=False, comment='Last day of the period month'),
        sa.Column('snapshot_data', JSONB, nullable=False, default={}, comment='Aggregated totals as JSON'),
        sa.Column('status', period_status_enum, nullable=False, server_default='LOCKED'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True, comment='Admin notes for the snapshot'),
    )
    
    # Unique constraint on (period_year, period_month)
    op.create_unique_constraint(
        'uq_period_snapshots_year_month',
        'period_snapshots',
        ['period_year', 'period_month']
    )
    
    # Index for faster lookups
    op.create_index('ix_period_snapshots_year_month', 'period_snapshots', ['period_year', 'period_month'])
    op.create_index('ix_period_snapshots_status', 'period_snapshots', ['status'])
    
    # Create period_unlock_logs table for audit trail
    op.create_table(
        'period_unlock_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('period_snapshot_id', sa.Integer(), sa.ForeignKey('period_snapshots.id'), nullable=False),
        sa.Column('unlocked_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False, comment='Reason for unlock (required)'),
        sa.Column('previous_status', sa.String(20), nullable=False),
    )
    
    op.create_index('ix_period_unlock_logs_snapshot_id', 'period_unlock_logs', ['period_snapshot_id'])


def downgrade():
    op.drop_table('period_unlock_logs')
    op.drop_table('period_snapshots')
    op.execute("DROP TYPE period_status")
