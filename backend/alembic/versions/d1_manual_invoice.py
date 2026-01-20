"""Add manual invoice fields

Revision ID: d1_manual_invoice
Revises: a43085327680, phase_a_001
Create Date: 2026-01-20

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd1_manual_invoice'
down_revision = ('a43085327680', 'phase_a_001')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add manual invoice fields
    # is_manual: distinguish manual from auto-generated invoices
    # manual_reason: description/reason for manual invoice
    # Note: created_by already exists in the table
    
    op.add_column('invoices', sa.Column('is_manual', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('invoices', sa.Column('manual_reason', sa.Text(), nullable=True))
    
    # For manual invoices, cycle_year and cycle_month should allow NULL
    # But we can't easily change NOT NULL constraint with data
    # Instead, we'll use a convention: manual invoices use cycle_year=0, cycle_month=0
    
    # Drop the unique constraint to allow multiple manual invoices per house
    # We need to recreate it with a condition or partial index
    try:
        op.drop_constraint('unique_house_cycle', 'invoices', type_='unique')
    except Exception:
        pass  # Constraint might not exist
    
    # Create new unique constraint that only applies to non-manual invoices
    # PostgreSQL supports partial unique indexes
    op.execute("""
        CREATE UNIQUE INDEX unique_house_cycle_non_manual 
        ON invoices (house_id, cycle_year, cycle_month) 
        WHERE is_manual = false
    """)


def downgrade() -> None:
    # Drop the partial unique index
    op.execute("DROP INDEX IF EXISTS unique_house_cycle_non_manual")
    
    # Recreate original constraint (will fail if manual invoices exist with cycle 0)
    # op.create_unique_constraint('unique_house_cycle', 'invoices', ['house_id', 'cycle_year', 'cycle_month'])
    
    op.drop_column('invoices', 'manual_reason')
    op.drop_column('invoices', 'is_manual')
