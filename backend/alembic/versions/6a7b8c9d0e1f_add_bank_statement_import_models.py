"""add bank statement import models

Revision ID: 6a7b8c9d0e1f
Revises: 580148e2242d
Create Date: 2026-01-15 15:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6a7b8c9d0e1f'
down_revision: Union[str, Sequence[str], None] = '3842778e4ed8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add bank statement import tables."""
    
    # Create bank_accounts table
    op.create_table(
        'bank_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bank_code', sa.String(length=50), nullable=False),
        sa.Column('account_no_masked', sa.String(length=50), nullable=False),
        sa.Column('account_type', sa.String(length=20), nullable=False),  # Use string instead of enum
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create bank_statement_batches table
    op.create_table(
        'bank_statement_batches',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bank_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(length=20), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),  # Use string instead of enum
        sa.Column('date_range_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('date_range_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('opening_balance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('closing_balance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('warnings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['bank_account_id'], ['bank_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bank_account_id', 'year', 'month', name='uq_bank_account_year_month')
    )
    
    # Create bank_transactions table
    op.create_table(
        'bank_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bank_statement_batch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('bank_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('effective_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('debit', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('credit', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('balance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('channel', sa.String(length=100), nullable=True),
        sa.Column('raw_row', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('fingerprint', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['bank_account_id'], ['bank_accounts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bank_statement_batch_id'], ['bank_statement_batches.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bank_account_id', 'fingerprint', name='uq_bank_account_fingerprint')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_bank_transactions_effective_at', 'bank_transactions', ['effective_at'])
    op.create_index('ix_bank_transactions_batch_id', 'bank_transactions', ['bank_statement_batch_id'])


def downgrade() -> None:
    """Downgrade schema - remove bank statement import tables."""
    
    # Drop indexes
    op.drop_index('ix_bank_transactions_batch_id', table_name='bank_transactions')
    op.drop_index('ix_bank_transactions_effective_at', table_name='bank_transactions')
    
    # Drop tables
    op.drop_table('bank_transactions')
    op.drop_table('bank_statement_batches')
    op.drop_table('bank_accounts')
