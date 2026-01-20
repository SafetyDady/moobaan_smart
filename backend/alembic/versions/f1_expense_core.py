"""Phase F.1: Expense Core (Cash Out)

Revision ID: f1_expense_core
Revises: d4_promotion_policies
Create Date: 2026-01-20

This migration updates the expenses table for production use:
- Add status enum (PENDING, PAID, CANCELLED)
- Add house_id FK (nullable - expense may relate to a specific house)
- Add expense_date (when expense occurred)
- Add paid_date (when actually paid)
- Add vendor_name, payment_method
- Add indexes for reporting

Rules:
- amount > 0
- paid_date cannot be earlier than expense_date
- Cannot mark-paid if status is CANCELLED
- Cannot cancel if already PAID
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'f1_expense_core'
down_revision = 'd4_promotion_policies'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create expense_status enum
    expense_status = postgresql.ENUM('PENDING', 'PAID', 'CANCELLED', name='expense_status', create_type=False)
    expense_status.create(op.get_bind(), checkfirst=True)
    
    # Add new columns to expenses table
    # Note: The expenses table already exists with basic fields from initial migration
    
    # Add house_id FK (nullable - expense may relate to a specific house)
    op.add_column('expenses', sa.Column('house_id', sa.Integer(), sa.ForeignKey('houses.id', ondelete='SET NULL'), nullable=True))
    
    # Add status column with default PENDING
    op.add_column('expenses', sa.Column('status', expense_status, nullable=False, server_default='PENDING'))
    
    # Add paid_date (when actually paid)
    op.add_column('expenses', sa.Column('paid_date', sa.Date(), nullable=True))
    
    # Add vendor_name
    op.add_column('expenses', sa.Column('vendor_name', sa.String(255), nullable=True))
    
    # Add payment_method (CASH/TRANSFER/CHECK/OTHER)
    op.add_column('expenses', sa.Column('payment_method', sa.String(50), nullable=True))
    
    # Add created_by_user_id FK
    op.add_column('expenses', sa.Column('created_by_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    
    # Rename expense_date column from DateTime to Date type
    # First drop the old column and add new one
    op.drop_column('expenses', 'expense_date')
    op.add_column('expenses', sa.Column('expense_date', sa.Date(), nullable=False, server_default=sa.func.current_date()))
    
    # Create indexes for reporting
    op.create_index('ix_expenses_expense_date', 'expenses', ['expense_date'])
    op.create_index('ix_expenses_status', 'expenses', ['status'])
    op.create_index('ix_expenses_house_id', 'expenses', ['house_id'])
    op.create_index('ix_expenses_category', 'expenses', ['category'])
    
    # Add check constraint for positive amount
    op.create_check_constraint('expense_amount_positive', 'expenses', 'amount > 0')


def downgrade() -> None:
    # Drop check constraint
    op.drop_constraint('expense_amount_positive', 'expenses')
    
    # Drop indexes
    op.drop_index('ix_expenses_category')
    op.drop_index('ix_expenses_house_id')
    op.drop_index('ix_expenses_status')
    op.drop_index('ix_expenses_expense_date')
    
    # Drop new columns
    op.drop_column('expenses', 'expense_date')
    op.add_column('expenses', sa.Column('expense_date', sa.DateTime(timezone=True), nullable=False))
    
    op.drop_column('expenses', 'created_by_user_id')
    op.drop_column('expenses', 'payment_method')
    op.drop_column('expenses', 'vendor_name')
    op.drop_column('expenses', 'paid_date')
    op.drop_column('expenses', 'status')
    op.drop_column('expenses', 'house_id')
    
    # Drop enum
    op.execute("DROP TYPE expense_status")
