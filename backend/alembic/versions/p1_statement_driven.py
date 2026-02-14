"""Phase 1: Statement-Driven Confirm & Post

1. BankTransaction: Add posting_status enum (UNMATCHED/MATCHED/POSTED/REVERSED)
2. IncomeTransaction: Make payin_id nullable, add status/reversed fields,
   add UNIQUE constraint on bank_transaction_id
3. InvoicePayment: Add status field for reverse support

Revision ID: p1_statement_driven
Revises: h13_attachments
Create Date: 2026-02-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers
revision = 'p1_statement_driven'
down_revision = 'h13_attachments'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. BankTransaction: posting_status ──
    posting_status_enum = sa.Enum(
        'UNMATCHED', 'MATCHED', 'POSTED', 'REVERSED',
        name='posting_status_enum'
    )
    posting_status_enum.create(op.get_bind(), checkfirst=True)
    
    op.add_column('bank_transactions', sa.Column(
        'posting_status',
        posting_status_enum,
        nullable=True,  # Add nullable first, backfill, then set default
        server_default='UNMATCHED',
    ))
    
    # Backfill existing rows: if matched_payin_id is NOT NULL → MATCHED, else UNMATCHED
    op.execute("""
        UPDATE bank_transactions 
        SET posting_status = CASE 
            WHEN matched_payin_id IS NOT NULL THEN 'MATCHED'::posting_status_enum
            ELSE 'UNMATCHED'::posting_status_enum
        END
        WHERE posting_status IS NULL
    """)
    
    # Also mark any that already have IncomeTransactions as POSTED
    op.execute("""
        UPDATE bank_transactions bt
        SET posting_status = 'POSTED'::posting_status_enum
        FROM income_transactions it
        WHERE it.reference_bank_transaction_id = bt.id
    """)
    
    # Now make NOT NULL
    op.alter_column('bank_transactions', 'posting_status', nullable=False)
    
    # ── 2. IncomeTransaction: make payin_id nullable ──
    # Drop the existing unique constraint on payin_id first
    op.drop_constraint('income_transactions_payin_id_key', 'income_transactions', type_='unique')
    
    # Make payin_id nullable (for Case B: statement without pay-in)
    op.alter_column('income_transactions', 'payin_id',
        existing_type=sa.Integer(),
        nullable=True,
    )
    
    # Re-add unique constraint (still 1:1 but nullable)
    op.create_unique_constraint('uq_income_txn_payin_id', 'income_transactions', ['payin_id'])
    
    # Add UNIQUE constraint on reference_bank_transaction_id 
    # (1 BankTransaction → max 1 IncomeTransaction)
    op.create_unique_constraint(
        'uq_income_txn_bank_txn_id',
        'income_transactions',
        ['reference_bank_transaction_id']
    )
    
    # Add status field for reverse support
    ledger_status_enum = sa.Enum('POSTED', 'REVERSED', name='ledger_status_enum')
    ledger_status_enum.create(op.get_bind(), checkfirst=True)
    
    op.add_column('income_transactions', sa.Column(
        'status', ledger_status_enum,
        nullable=True, server_default='POSTED'
    ))
    op.execute("UPDATE income_transactions SET status = 'POSTED' WHERE status IS NULL")
    op.alter_column('income_transactions', 'status', nullable=False)
    
    op.add_column('income_transactions', sa.Column(
        'reversed_at', sa.DateTime(timezone=True), nullable=True
    ))
    op.add_column('income_transactions', sa.Column(
        'reversed_by', sa.Integer(),
        sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    ))
    op.add_column('income_transactions', sa.Column(
        'reverse_reason', sa.Text(), nullable=True
    ))
    
    # ── 3. InvoicePayment: status field for reverse ──
    payment_status_enum = sa.Enum('ACTIVE', 'REVERSED', name='payment_status_enum')
    payment_status_enum.create(op.get_bind(), checkfirst=True)
    
    op.add_column('invoice_payments', sa.Column(
        'status', payment_status_enum,
        nullable=True, server_default='ACTIVE'
    ))
    op.execute("UPDATE invoice_payments SET status = 'ACTIVE' WHERE status IS NULL")
    op.alter_column('invoice_payments', 'status', nullable=False)


def downgrade() -> None:
    # ── 3. InvoicePayment: remove status ──
    op.drop_column('invoice_payments', 'status')
    sa.Enum(name='payment_status_enum').drop(op.get_bind(), checkfirst=True)
    
    # ── 2. IncomeTransaction: revert ──
    op.drop_column('income_transactions', 'reverse_reason')
    op.drop_column('income_transactions', 'reversed_by')
    op.drop_column('income_transactions', 'reversed_at')
    op.drop_column('income_transactions', 'status')
    sa.Enum(name='ledger_status_enum').drop(op.get_bind(), checkfirst=True)
    
    op.drop_constraint('uq_income_txn_bank_txn_id', 'income_transactions', type_='unique')
    op.drop_constraint('uq_income_txn_payin_id', 'income_transactions', type_='unique')
    
    op.alter_column('income_transactions', 'payin_id',
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.create_unique_constraint('income_transactions_payin_id_key', 'income_transactions', ['payin_id'])
    
    # ── 1. BankTransaction: remove posting_status ──
    op.drop_column('bank_transactions', 'posting_status')
    sa.Enum(name='posting_status_enum').drop(op.get_bind(), checkfirst=True)
