"""Attachments table for operational evidence

Single table: entity_type (PAYIN/EXPENSE) + file_type (SLIP/INVOICE/RECEIPT).
Soft delete only. No versioning.

Revision ID: h13_attachments
Revises: h12_expense_bank_alloc
Create Date: 2026-02-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = 'h13_attachments'
down_revision = 'h12_expense_bank_alloc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'attachments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(20), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('file_type', sa.String(20), nullable=False),
        sa.Column('original_filename', sa.String(500), nullable=True),
        sa.Column('content_type', sa.String(100), nullable=True),
        sa.Column('object_key', sa.String(1000), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )

    op.create_index('ix_attachment_entity', 'attachments', ['entity_type', 'entity_id'])


def downgrade() -> None:
    op.drop_index('ix_attachment_entity', table_name='attachments')
    op.drop_table('attachments')
