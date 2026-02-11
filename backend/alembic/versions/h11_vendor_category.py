"""Phase H.1.1: Vendor & Category Foundation

Create vendors, vendor_categories, expense_categories tables.
Add nullable vendor_id FK to expenses table.
Add case-insensitive unique indexes on name columns.
Seed default expense categories from hardcoded list.

Revision ID: h11_vendor_category
Revises: d41_line_user_id
Create Date: 2026-02-11
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'h11_vendor_category'
down_revision = 'd41_line_user_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create vendor_categories table
    op.create_table(
        'vendor_categories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_vendor_categories_id', 'vendor_categories', ['id'])
    # Case-insensitive unique index on name
    op.execute(
        "CREATE UNIQUE INDEX ix_vendor_categories_name_ci ON vendor_categories (LOWER(TRIM(name)))"
    )

    # 2. Create vendors table
    op.create_table(
        'vendors',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('vendor_category_id', sa.Integer(), sa.ForeignKey('vendor_categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('bank_account', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_vendors_id', 'vendors', ['id'])
    op.create_index('ix_vendors_vendor_category_id', 'vendors', ['vendor_category_id'])
    # Case-insensitive unique index on name
    op.execute(
        "CREATE UNIQUE INDEX ix_vendors_name_ci ON vendors (LOWER(TRIM(name)))"
    )

    # 3. Create expense_categories table
    op.create_table(
        'expense_categories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_expense_categories_id', 'expense_categories', ['id'])
    # Case-insensitive unique index on name
    op.execute(
        "CREATE UNIQUE INDEX ix_expense_categories_name_ci ON expense_categories (LOWER(TRIM(name)))"
    )

    # 4. Add nullable vendor_id FK to expenses table (NON-DESTRUCTIVE)
    # Keep existing vendor_name column as-is for backward compatibility
    op.add_column('expenses', sa.Column('vendor_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_expenses_vendor_id',
        'expenses', 'vendors',
        ['vendor_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_expenses_vendor_id', 'expenses', ['vendor_id'])

    # 5. Seed default expense categories from existing hardcoded list (idempotent)
    op.execute("""
        INSERT INTO expense_categories (name) VALUES
        ('MAINTENANCE'),
        ('SECURITY'),
        ('CLEANING'),
        ('UTILITIES'),
        ('ADMIN'),
        ('OTHER')
        ON CONFLICT (LOWER(TRIM(name))) DO NOTHING
    """)

    # 6. Seed default vendor categories (idempotent)
    op.execute("""
        INSERT INTO vendor_categories (name) VALUES
        ('Contractor'),
        ('Utility Provider'),
        ('Service Provider'),
        ('Supplier'),
        ('Other')
        ON CONFLICT (LOWER(TRIM(name))) DO NOTHING
    """)


def downgrade() -> None:
    # Remove vendor_id FK from expenses
    op.drop_constraint('fk_expenses_vendor_id', 'expenses', type_='foreignkey')
    op.drop_index('ix_expenses_vendor_id', 'expenses')
    op.drop_column('expenses', 'vendor_id')

    # Drop tables
    op.drop_index('ix_expense_categories_name_ci', 'expense_categories')
    op.drop_index('ix_expense_categories_id', 'expense_categories')
    op.drop_table('expense_categories')

    op.drop_index('ix_vendors_name_ci', 'vendors')
    op.drop_index('ix_vendors_vendor_category_id', 'vendors')
    op.drop_index('ix_vendors_id', 'vendors')
    op.drop_table('vendors')

    op.drop_index('ix_vendor_categories_name_ci', 'vendor_categories')
    op.drop_index('ix_vendor_categories_id', 'vendor_categories')
    op.drop_table('vendor_categories')
