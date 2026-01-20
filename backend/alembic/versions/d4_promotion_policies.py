"""
Phase D.4: Promotion Policy Layer - Migration

Creates promotion_policies table for storing promotion rules.
Promotions are POLICY-ONLY - they suggest credits but never auto-apply.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision = 'd4_promotion_policies'
down_revision = 'd2_credit_notes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create promotion_scope enum
    promotion_scope_enum = postgresql.ENUM(
        'project', 'village', 'house',
        name='promotion_scope',
        create_type=False
    )
    
    # Create enum type first
    op.execute("CREATE TYPE promotion_scope AS ENUM ('project', 'village', 'house')")
    
    # Create promotion_status enum
    op.execute("CREATE TYPE promotion_status AS ENUM ('active', 'expired', 'disabled')")
    
    # Create promotion_policies table
    op.create_table(
        'promotion_policies',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('code', sa.String(50), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Validity period
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_to', sa.Date(), nullable=False),
        
        # Eligibility criteria
        sa.Column('min_payin_amount', sa.Numeric(12, 2), nullable=True),
        
        # Credit calculation (one of these)
        sa.Column('credit_amount', sa.Numeric(10, 2), nullable=True),  # Fixed amount
        sa.Column('credit_percent', sa.Numeric(5, 2), nullable=True),  # Percentage (0-100)
        
        # Limits
        sa.Column('max_credit_total', sa.Numeric(12, 2), nullable=True),
        
        # Scope
        sa.Column('scope', postgresql.ENUM('project', 'village', 'house', name='promotion_scope', create_type=False), 
                  nullable=False, server_default='project'),
        sa.Column('scope_id', sa.Integer(), nullable=True),  # FK to village/house if scoped
        
        # Status
        sa.Column('status', postgresql.ENUM('active', 'expired', 'disabled', name='promotion_status', create_type=False),
                  nullable=False, server_default='active'),
        
        # Audit
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        # Constraints
        sa.CheckConstraint(
            '(credit_amount IS NOT NULL AND credit_percent IS NULL) OR '
            '(credit_amount IS NULL AND credit_percent IS NOT NULL)',
            name='chk_credit_type'
        ),
        sa.CheckConstraint('credit_percent IS NULL OR (credit_percent >= 0 AND credit_percent <= 100)', 
                          name='chk_credit_percent_range'),
        sa.CheckConstraint('valid_to >= valid_from', name='chk_valid_dates'),
    )
    
    # Create indexes
    op.create_index('ix_promotion_policies_code', 'promotion_policies', ['code'])
    op.create_index('ix_promotion_policies_status', 'promotion_policies', ['status'])
    op.create_index('ix_promotion_policies_valid_dates', 'promotion_policies', ['valid_from', 'valid_to'])


def downgrade() -> None:
    op.drop_index('ix_promotion_policies_valid_dates')
    op.drop_index('ix_promotion_policies_status')
    op.drop_index('ix_promotion_policies_code')
    op.drop_table('promotion_policies')
    op.execute("DROP TYPE IF EXISTS promotion_status")
    op.execute("DROP TYPE IF EXISTS promotion_scope")
