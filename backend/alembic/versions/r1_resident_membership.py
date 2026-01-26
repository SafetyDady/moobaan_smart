"""
Phase R.1 (Step 1): Resident Membership Migration

Creates the resident_memberships table.

IMPORTANT:
- Additive only - no changes to existing tables
- No cascade delete - preserve audit trail
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

revision = 'r1_resident_membership'
down_revision = 'g2_export_audit_log'
branch_labels = None
depends_on = None


def upgrade():
    # Create enums
    membership_status = ENUM('ACTIVE', 'INACTIVE', name='residentmembershipstatus', create_type=False)
    membership_role = ENUM('OWNER', 'FAMILY', name='residentmembershiprole', create_type=False)
    
    # Create enums in database
    membership_status.create(op.get_bind(), checkfirst=True)
    membership_role.create(op.get_bind(), checkfirst=True)
    
    # Create table
    op.create_table(
        'resident_memberships',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('house_id', sa.Integer(), nullable=False),
        sa.Column('status', membership_status, nullable=False, server_default='ACTIVE'),
        sa.Column('role', membership_role, nullable=False, server_default='FAMILY'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deactivated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['house_id'], ['houses.id'], ondelete='RESTRICT'),
        sa.UniqueConstraint('user_id', 'house_id', name='uq_resident_membership_user_house')
    )
    
    # Create indexes
    op.create_index('ix_resident_memberships_user_id', 'resident_memberships', ['user_id'])
    op.create_index('ix_resident_memberships_house_id', 'resident_memberships', ['house_id'])
    op.create_index('ix_resident_memberships_status', 'resident_memberships', ['status'])


def downgrade():
    op.drop_index('ix_resident_memberships_status', 'resident_memberships')
    op.drop_index('ix_resident_memberships_house_id', 'resident_memberships')
    op.drop_index('ix_resident_memberships_user_id', 'resident_memberships')
    op.drop_table('resident_memberships')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS residentmembershipstatus')
    op.execute('DROP TYPE IF EXISTS residentmembershiprole')
