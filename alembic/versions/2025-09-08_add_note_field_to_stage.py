"""add note field to stage

Revision ID: a1b2c3d4e5f6
Revises: ce66c21b6a7e
Create Date: 2025-09-08 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "ce66c21b6a7e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("stage", sa.Column("note", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("stage", "note")
