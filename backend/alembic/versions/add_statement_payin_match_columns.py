"""add statement payin match columns

Revision ID: add_statement_match
Revises: 
Create Date: 2026-01-16 12:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_statement_match'
down_revision = None  # Update this to latest revision
branch_labels = None
depends_on = None


def upgrade():
    # Add matched_payin_id to bank_transactions (nullable, unique)
    op.add_column('bank_transactions', 
        sa.Column('matched_payin_id', sa.Integer(), nullable=True)
    )
    op.create_unique_constraint(
        'uq_bank_transaction_matched_payin',
        'bank_transactions',
        ['matched_payin_id']
    )
    op.create_foreign_key(
        'fk_bank_transaction_matched_payin',
        'bank_transactions',
        'payin_reports',
        ['matched_payin_id'],
        ['id'],
        ondelete='SET NULL'
    )
    
    # Add matched_statement_txn_id to payin_reports (nullable, unique)
    op.add_column('payin_reports',
        sa.Column('matched_statement_txn_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_unique_constraint(
        'uq_payin_matched_statement_txn',
        'payin_reports',
        ['matched_statement_txn_id']
    )
    op.create_foreign_key(
        'fk_payin_matched_statement_txn',
        'payin_reports',
        'bank_transactions',
        ['matched_statement_txn_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    # Drop foreign keys first
    op.drop_constraint('fk_payin_matched_statement_txn', 'payin_reports', type_='foreignkey')
    op.drop_constraint('uq_payin_matched_statement_txn', 'payin_reports', type_='unique')
    op.drop_column('payin_reports', 'matched_statement_txn_id')
    
    op.drop_constraint('fk_bank_transaction_matched_payin', 'bank_transactions', type_='foreignkey')
    op.drop_constraint('uq_bank_transaction_matched_payin', 'bank_transactions', type_='unique')
    op.drop_column('bank_transactions', 'matched_payin_id')
