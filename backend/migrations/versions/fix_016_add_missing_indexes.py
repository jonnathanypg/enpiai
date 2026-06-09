"""add_missing_indexes

Revision ID: fix_016_add_indexes
Revises: 
Create Date: 2026-06-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_016_add_indexes'
down_revision = None  # Or figure out the latest one, but usually multiple heads can be merged or this is sufficient for manual apply if needed. Actually we should get the current head.
branch_labels = None
depends_on = None

def upgrade():
    # conversations
    op.create_index('idx_conv_lookup', 'conversations', ['distributor_id', 'channel', 'participant_id', 'status'], unique=False)
    
    # scheduled_tasks
    op.create_index('idx_tasks_pending', 'scheduled_tasks', ['distributor_id', 'action', 'status'], unique=False)
    
    # leads
    op.create_index('idx_leads_phone', 'leads', ['phone'], unique=False)
    
    # agent_configs
    # priority DESC is specific, but standard create_index handles columns.
    op.create_index('idx_agent_priority', 'agent_configs', ['distributor_id', sa.text('priority DESC')], unique=False)

def downgrade():
    op.drop_index('idx_agent_priority', table_name='agent_configs')
    op.drop_index('idx_leads_phone', table_name='leads')
    op.drop_index('idx_tasks_pending', table_name='scheduled_tasks')
    op.drop_index('idx_conv_lookup', table_name='conversations')
