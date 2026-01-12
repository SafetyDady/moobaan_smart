"""Initial tables - houses, users, house_members, payin_reports

Revision ID: 47578bf954a5
Revises: 
Create Date: 2026-01-12 16:52:27.388188

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47578bf954a5'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create houses table
    op.create_table('houses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('house_no', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('floor_area', sa.String(length=50), nullable=True),
        sa.Column('land_area', sa.String(length=50), nullable=True),
        sa.Column('zone', sa.String(length=10), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('house_no')
    )
    op.create_index(op.f('ix_houses_id'), 'houses', ['id'], unique=False)
    op.create_index(op.f('ix_houses_house_no'), 'houses', ['house_no'], unique=True)
    
    # Create house_members table
    op.create_table('house_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('house_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('member_role', sa.String(length=50), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['house_id'], ['houses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_house_members_id'), 'house_members', ['id'], unique=False)
    
    # Create payin_reports table
    op.create_table('payin_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('house_id', sa.Integer(), nullable=False),
        sa.Column('submitted_by_user_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('transfer_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('transfer_hour', sa.Integer(), nullable=False),
        sa.Column('transfer_minute', sa.Integer(), nullable=False),
        sa.Column('slip_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['house_id'], ['houses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['submitted_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payin_reports_id'), 'payin_reports', ['id'], unique=False)
    
    # Create placeholder tables for future use
    
    # Create invoices table
    op.create_table('invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_no', sa.String(length=50), nullable=False),
        sa.Column('house_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['house_id'], ['houses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_no')
    )
    op.create_index(op.f('ix_invoices_id'), 'invoices', ['id'], unique=False)
    op.create_index(op.f('ix_invoices_invoice_no'), 'invoices', ['invoice_no'], unique=True)
    
    # Create invoice_items table
    op.create_table('invoice_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_recurring', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoice_items_id'), 'invoice_items', ['id'], unique=False)
    
    # Create expenses table
    op.create_table('expenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('expense_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('receipt_url', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_expenses_id'), 'expenses', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('expenses')
    op.drop_table('invoice_items')
    op.drop_table('invoices')
    op.drop_table('payin_reports')
    op.drop_table('house_members')
    op.drop_table('houses')
    op.drop_table('users')
