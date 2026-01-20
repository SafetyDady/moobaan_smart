"""Phase D.2: Credit Notes table

Revision ID: d2_credit_notes
Revises: d1_manual_invoice
Create Date: 2026-01-20

This migration creates the credit_notes table for adjusting invoice amounts
without modifying the original invoice record (immutable accounting).

Rules:
- Credit notes CANNOT be updated or deleted after creation
- credit_amount must be positive and <= remaining balance
- is_full_credit = true cancels the entire invoice
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'd2_credit_notes'
down_revision = 'd1_manual_invoice'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create credit_note_status enum first
    credit_note_status = postgresql.ENUM('issued', 'applied', name='credit_note_status', create_type=False)
    credit_note_status.create(op.get_bind(), checkfirst=True)
    
    # Create credit_notes table
    op.create_table(
        'credit_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), sa.ForeignKey('invoices.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('credit_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('is_full_credit', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', credit_note_status, nullable=False, server_default='applied'),
        sa.Column('created_by_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('credit_amount > 0', name='credit_amount_positive')
    )
    
    # Create index for faster lookup by invoice_id
    op.create_index('ix_credit_notes_invoice_id', 'credit_notes', ['invoice_id'])


def downgrade() -> None:
    op.drop_index('ix_credit_notes_invoice_id')
    op.drop_table('credit_notes')
    op.execute("DROP TYPE credit_note_status")
