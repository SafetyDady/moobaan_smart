"""Phase A: Pay-in State Machine + Admin-created Pay-in

Revision ID: phase_a_001
Revises: 
Create Date: 2026-01-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase_a_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new enum values to payinstatus
    # PostgreSQL requires special handling for enum types
    
    # First, add new enum values (if using PostgreSQL)
    op.execute("ALTER TYPE payinstatus ADD VALUE IF NOT EXISTS 'DRAFT'")
    op.execute("ALTER TYPE payinstatus ADD VALUE IF NOT EXISTS 'SUBMITTED'")
    op.execute("ALTER TYPE payinstatus ADD VALUE IF NOT EXISTS 'REJECTED_NEEDS_FIX'")
    
    # Create payinsource enum type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE payinsource AS ENUM ('RESIDENT', 'ADMIN_CREATED', 'LINE_RECEIVED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Add new columns to payin_reports
    op.add_column('payin_reports', 
        sa.Column('source', postgresql.ENUM('RESIDENT', 'ADMIN_CREATED', 'LINE_RECEIVED', name='payinsource', create_type=False), 
                  nullable=True, server_default='RESIDENT'))
    
    op.add_column('payin_reports',
        sa.Column('created_by_admin_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    
    op.add_column('payin_reports',
        sa.Column('admin_note', sa.Text(), nullable=True))
    
    op.add_column('payin_reports',
        sa.Column('reference_bank_transaction_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('bank_transactions.id', ondelete='SET NULL'), nullable=True))
    
    op.add_column('payin_reports',
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True))
    
    # Update existing PENDING records to SUBMITTED for consistency
    op.execute("UPDATE payin_reports SET source = 'RESIDENT' WHERE source IS NULL")
    op.execute("UPDATE payin_reports SET status = 'SUBMITTED' WHERE status = 'PENDING'")
    op.execute("UPDATE payin_reports SET status = 'REJECTED_NEEDS_FIX' WHERE status = 'REJECTED'")
    
    # Make source NOT NULL after setting defaults
    op.alter_column('payin_reports', 'source', nullable=False)


def downgrade() -> None:
    # Revert status values
    op.execute("UPDATE payin_reports SET status = 'PENDING' WHERE status = 'SUBMITTED'")
    op.execute("UPDATE payin_reports SET status = 'REJECTED' WHERE status = 'REJECTED_NEEDS_FIX'")
    
    # Drop new columns
    op.drop_column('payin_reports', 'submitted_at')
    op.drop_column('payin_reports', 'reference_bank_transaction_id')
    op.drop_column('payin_reports', 'admin_note')
    op.drop_column('payin_reports', 'created_by_admin_id')
    op.drop_column('payin_reports', 'source')
    
    # Note: Cannot easily remove enum values in PostgreSQL
    # The enum type and values will remain
