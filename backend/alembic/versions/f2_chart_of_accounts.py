"""Phase F.2: Chart of Accounts (COA Lite)

Revision ID: f2_chart_of_accounts
Revises: f1_expense_core
Create Date: 2026-01-20

This migration creates the Chart of Accounts structure:
- chart_of_accounts table with account_code, account_name, account_type
- Add account_id FK to expenses (must be EXPENSE type)
- Add revenue_account_id FK to invoices (must be REVENUE type)

IMPORTANT: This is COA LITE - NO GL, NO posting, NO balance tracking
Purpose: Classification, Reporting, Excel Export only
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'f2_chart_of_accounts'
down_revision = 'f1_expense_core'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create account_type enum
    account_type = postgresql.ENUM('ASSET', 'LIABILITY', 'REVENUE', 'EXPENSE', name='account_type', create_type=False)
    account_type.create(op.get_bind(), checkfirst=True)
    
    # Create chart_of_accounts table
    op.create_table(
        'chart_of_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_code', sa.String(20), nullable=False),
        sa.Column('account_name', sa.String(255), nullable=False),
        sa.Column('account_type', account_type, nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_chart_of_accounts_account_code', 'chart_of_accounts', ['account_code'], unique=True)
    op.create_index('ix_chart_of_accounts_account_type', 'chart_of_accounts', ['account_type'])
    op.create_index('ix_chart_of_accounts_active', 'chart_of_accounts', ['active'])
    
    # Add account_id FK to expenses (nullable for existing data)
    op.add_column('expenses', sa.Column('account_id', sa.Integer(), sa.ForeignKey('chart_of_accounts.id', ondelete='RESTRICT'), nullable=True))
    op.create_index('ix_expenses_account_id', 'expenses', ['account_id'])
    
    # Add revenue_account_id FK to invoices (nullable for existing data)
    op.add_column('invoices', sa.Column('revenue_account_id', sa.Integer(), sa.ForeignKey('chart_of_accounts.id', ondelete='RESTRICT'), nullable=True))
    op.create_index('ix_invoices_revenue_account_id', 'invoices', ['revenue_account_id'])
    
    # Seed default accounts
    op.execute("""
        INSERT INTO chart_of_accounts (account_code, account_name, account_type, active) VALUES
        -- Revenue Accounts (4xxx)
        ('4101', 'ค่าส่วนกลาง (Common Fee)', 'REVENUE', true),
        ('4102', 'ค่าน้ำประปา (Water Fee)', 'REVENUE', true),
        ('4103', 'ค่าขยะ (Waste Fee)', 'REVENUE', true),
        ('4104', 'ค่าปรับล่าช้า (Late Fee)', 'REVENUE', true),
        ('4199', 'รายได้อื่นๆ (Other Revenue)', 'REVENUE', true),
        -- Expense Accounts (5xxx)
        ('5101', 'ค่าไฟฟ้าส่วนกลาง (Common Electricity)', 'EXPENSE', true),
        ('5102', 'ค่าน้ำส่วนกลาง (Common Water)', 'EXPENSE', true),
        ('5103', 'ค่ารักษาความปลอดภัย (Security)', 'EXPENSE', true),
        ('5104', 'ค่าทำความสะอาด (Cleaning)', 'EXPENSE', true),
        ('5105', 'ค่าดูแลสวน (Gardening)', 'EXPENSE', true),
        ('5106', 'ค่าซ่อมบำรุง (Maintenance)', 'EXPENSE', true),
        ('5107', 'ค่าบริหารจัดการ (Admin)', 'EXPENSE', true),
        ('5199', 'ค่าใช้จ่ายอื่นๆ (Other Expense)', 'EXPENSE', true),
        -- Asset Accounts (1xxx) - for future use
        ('1101', 'เงินสดในมือ (Cash on Hand)', 'ASSET', true),
        ('1102', 'เงินฝากธนาคาร (Bank Account)', 'ASSET', true),
        ('1201', 'ลูกหนี้ค่าส่วนกลาง (AR - Common Fee)', 'ASSET', true),
        -- Liability Accounts (2xxx) - for future use
        ('2101', 'เจ้าหนี้การค้า (Accounts Payable)', 'LIABILITY', true),
        ('2102', 'รายได้รับล่วงหน้า (Unearned Revenue)', 'LIABILITY', true)
    """)


def downgrade() -> None:
    # Drop indexes and FKs first
    op.drop_index('ix_invoices_revenue_account_id')
    op.drop_column('invoices', 'revenue_account_id')
    
    op.drop_index('ix_expenses_account_id')
    op.drop_column('expenses', 'account_id')
    
    # Drop chart_of_accounts table
    op.drop_index('ix_chart_of_accounts_active')
    op.drop_index('ix_chart_of_accounts_account_type')
    op.drop_index('ix_chart_of_accounts_account_code')
    op.drop_table('chart_of_accounts')
    
    # Drop enum
    op.execute("DROP TYPE account_type")
