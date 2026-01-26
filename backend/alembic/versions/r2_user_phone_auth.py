"""
Phase R.2 (Step 2): User Phone-Only Support Migration

Modifies users table to support OTP-based resident login:
- Make email nullable (residents use phone only)
- Make hashed_password nullable (residents use OTP only)  
- Add unique index on phone
- Add username column for display

IMPORTANT:
- Backward compatible - existing users with email continue to work
- No data loss - only adding flexibility
"""

from alembic import op
import sqlalchemy as sa

revision = 'r2_user_phone_auth'
down_revision = 'r1_resident_membership'
branch_labels = None
depends_on = None


def upgrade():
    # Make email nullable for residents (phone-only)
    op.alter_column('users', 'email',
        existing_type=sa.String(255),
        nullable=True
    )
    
    # Make hashed_password nullable for residents (OTP-only)
    op.alter_column('users', 'hashed_password',
        existing_type=sa.String(255),
        nullable=True
    )
    
    # Add username column (for display, auto-generated for residents)
    op.add_column('users', 
        sa.Column('username', sa.String(100), nullable=True)
    )
    
    # Create unique index on phone (for OTP lookup)
    # Note: Unique partial index - only for non-null phones
    op.execute("""
        CREATE UNIQUE INDEX ix_users_phone_unique 
        ON users (phone) 
        WHERE phone IS NOT NULL
    """)
    
    # Populate username for existing users
    op.execute("""
        UPDATE users 
        SET username = COALESCE(full_name, email)
        WHERE username IS NULL
    """)


def downgrade():
    # Drop phone unique index
    op.drop_index('ix_users_phone_unique', table_name='users')
    
    # Drop username column
    op.drop_column('users', 'username')
    
    # Restore NOT NULL constraints
    # First, set default values for any nulls
    op.execute("""
        UPDATE users 
        SET email = 'placeholder_' || id || '@resident.local'
        WHERE email IS NULL
    """)
    op.execute("""
        UPDATE users 
        SET hashed_password = 'OTP_ONLY_NO_PASSWORD'
        WHERE hashed_password IS NULL
    """)
    
    op.alter_column('users', 'email',
        existing_type=sa.String(255),
        nullable=False
    )
    
    op.alter_column('users', 'hashed_password',
        existing_type=sa.String(255),
        nullable=False
    )
