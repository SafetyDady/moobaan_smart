"""
Phase D.2: Add session_version for resident session revocation

This column allows admin to revoke all active sessions of a resident
by incrementing the version. JWT tokens include session_version,
and on every authenticated request we compare with DB value.
If mismatch → 401 SESSION_REVOKED.

Revision ID: d2_session_version
Revises: g2_export_audit_log
Create Date: 2026-02-04
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd2_session_version'
down_revision = '00071bc77452'
branch_labels = None
depends_on = None


def upgrade():
    # Add session_version column with default=1
    # This is used for resident session revocation
    op.add_column('users', sa.Column(
        'session_version',
        sa.Integer(),
        nullable=False,
        server_default='1',
        comment='Session version for resident session revocation. Increment to revoke all sessions.'
    ))


def downgrade():
    op.drop_column('users', 'session_version')
