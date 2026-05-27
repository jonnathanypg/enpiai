"""Add PLAYGROUND to ConversationChannel enum

Revision ID: a1b2c3d4e5f6
Revises: 42c79b1478de
Create Date: 2026-05-26 14:50:00.000000

Migration Path: Channel enums will be stored as plain strings in decentralized storage.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '42c79b1478de'
branch_labels = None
depends_on = None


def upgrade():
    # MySQL requires MODIFY COLUMN to alter ENUM values.
    # We add 'PLAYGROUND' to the existing set.
    op.execute(
        "ALTER TABLE conversations MODIFY COLUMN channel "
        "ENUM('WHATSAPP', 'TELEGRAM', 'WEBCHAT', 'EMAIL', 'INTERNAL', 'PLAYGROUND') NOT NULL"
    )


def downgrade():
    # Remove PLAYGROUND from the enum (only safe if no rows use it).
    op.execute(
        "ALTER TABLE conversations MODIFY COLUMN channel "
        "ENUM('WHATSAPP', 'TELEGRAM', 'WEBCHAT', 'EMAIL', 'INTERNAL') NOT NULL"
    )
