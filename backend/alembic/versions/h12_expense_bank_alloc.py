"""Expense Bank Allocation table

Create expense_bank_allocations junction table for matching
expenses to bank debit transactions (many-to-many, partial amounts).

Revision ID: h12_expense_bank_alloc
Revises: h11_vendor_category
Create Date: 2026-02-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers
revision = 'h12_expense_bank_alloc'
down_revision = 'h11_vendor_category'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'expense_bank_allocations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('expense_id', sa.Integer(), sa.ForeignKey('expenses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('bank_transaction_id', UUID(as_uuid=True), sa.ForeignKey('bank_transactions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('matched_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Unique constraint: one allocation per expense+bank_txn pair
    op.create_unique_constraint(
        'uq_expense_bank_allocation',
        'expense_bank_allocations',
        ['expense_id', 'bank_transaction_id']
    )

    # Check constraint: amount must be positive
    op.create_check_constraint(
        'ck_allocation_amount_positive',
        'expense_bank_allocations',
        'matched_amount > 0'
    )

    # Indexes for FK lookups
    op.create_index('ix_allocation_expense_id', 'expense_bank_allocations', ['expense_id'])
    op.create_index('ix_allocation_bank_txn_id', 'expense_bank_allocations', ['bank_transaction_id'])


def downgrade() -> None:
    op.drop_index('ix_allocation_bank_txn_id', table_name='expense_bank_allocations')
    op.drop_index('ix_allocation_expense_id', table_name='expense_bank_allocations')
    op.drop_constraint('ck_allocation_amount_positive', 'expense_bank_allocations', type_='check')
    op.drop_constraint('uq_expense_bank_allocation', 'expense_bank_allocations', type_='unique')
    op.drop_table('expense_bank_allocations')
