"""Add is_flagged field to purpose table

Revision ID: f8d9c5e4a7b2
Revises: be67b626ac24
Create Date: 2025-08-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8d9c5e4a7b2'
down_revision: Union[str, Sequence[str], None] = 'be67b626ac24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_flagged column to purpose table
    op.add_column('purpose', sa.Column('is_flagged', sa.Boolean(), nullable=False, server_default='false'))
    
    # Create index on is_flagged for efficient filtering
    op.create_index(op.f('ix_purpose_is_flagged'), 'purpose', ['is_flagged'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the index
    op.drop_index(op.f('ix_purpose_is_flagged'), table_name='purpose')
    
    # Drop the column
    op.drop_column('purpose', 'is_flagged')