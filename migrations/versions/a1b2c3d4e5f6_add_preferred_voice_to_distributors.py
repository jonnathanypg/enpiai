"""add preferred_voice to distributors

Revision ID: a1b2c3d4e5f6
Revises: b676c0601220
Create Date: 2026-05-28 07:32:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'b676c0601220'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('distributors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('preferred_voice', sa.String(length=100), nullable=True))


def downgrade():
    with op.batch_alter_table('distributors', schema=None) as batch_op:
        batch_op.drop_column('preferred_voice')
