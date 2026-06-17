"""merge heads

Revision ID: 23babbab9b22
Revises: a1b2c3d4e5f6, fix_016_add_indexes
Create Date: 2026-06-10 19:33:18.250505

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23babbab9b22'
down_revision = ('a1b2c3d4e5f6', 'fix_016_add_indexes')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
