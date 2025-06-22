"""add_indexes_for_performance

Revision ID: 8e2921d72c9e
Revises: 297142562641
Create Date: 2025-06-22 12:32:10.029895

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e2921d72c9e'
down_revision: Union[str, Sequence[str], None] = '297142562641'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add indexes for better performance in filtering and searching
    
    # Purpose table indexes
    op.create_index(op.f('ix_purpose_description'), 'purpose', ['description'], unique=False)
    op.create_index(op.f('ix_purpose_content'), 'purpose', ['content'], unique=False)
    op.create_index(op.f('ix_purpose_status'), 'purpose', ['status'], unique=False)
    op.create_index(op.f('ix_purpose_hierarchy_id'), 'purpose', ['hierarchy_id'], unique=False)
    op.create_index(op.f('ix_purpose_supplier_id'), 'purpose', ['supplier_id'], unique=False)
    op.create_index(op.f('ix_purpose_service_type_id'), 'purpose', ['service_type_id'], unique=False)
    
    # Hierarchy table indexes
    op.create_index(op.f('ix_hierarchy_path'), 'hierarchy', ['path'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove indexes
    op.drop_index(op.f('ix_purpose_description'), table_name='purpose')
    op.drop_index(op.f('ix_purpose_content'), table_name='purpose')
    op.drop_index(op.f('ix_purpose_status'), table_name='purpose')
    op.drop_index(op.f('ix_purpose_hierarchy_id'), table_name='purpose')
    op.drop_index(op.f('ix_purpose_supplier_id'), table_name='purpose')
    op.drop_index(op.f('ix_purpose_service_type_id'), table_name='purpose')
    
    op.drop_index(op.f('ix_hierarchy_path'), table_name='hierarchy')
