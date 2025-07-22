"""add_signed_and_partially_supplied_statuses

Revision ID: 2c70acc4859b
Revises: a5a4132ecf25
Create Date: 2025-07-22 10:59:08.935417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c70acc4859b'
down_revision: Union[str, Sequence[str], None] = '1198cd890fcc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new enum values to the existing statusenum type
    op.execute("ALTER TYPE statusenum ADD VALUE 'SIGNED'")
    op.execute("ALTER TYPE statusenum ADD VALUE 'PARTIALLY_SUPPLIED'")


def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL doesn't support removing enum values directly
    # To properly downgrade, we would need to:
    # 1. Create a new enum without the values
    # 2. Update all columns to use the new enum
    # 3. Drop the old enum
    # This is complex and potentially destructive, so we'll leave it as a no-op
    # In production, this would require careful planning
    pass
