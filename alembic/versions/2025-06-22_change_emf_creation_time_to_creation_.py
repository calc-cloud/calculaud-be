"""change_emf_creation_time_to_creation_date

Revision ID: db1116645e14
Revises: 4edbe6d330ef
Create Date: 2025-06-22 15:02:24.039317

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db1116645e14'
down_revision: Union[str, Sequence[str], None] = '4edbe6d330ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Change EMF creation_time column to creation_date and change type from DateTime to Date
    
    # First, add the new column
    op.add_column('emf', sa.Column('creation_date', sa.Date(), server_default=sa.text('current_date'), nullable=False))
    
    # Copy data from old column to new column (convert datetime to date)
    op.execute("UPDATE emf SET creation_date = DATE(creation_time)")
    
    # Drop the old column
    op.drop_column('emf', 'creation_time')


def downgrade() -> None:
    """Downgrade schema."""
    # Revert the changes - change creation_date back to creation_time and change type from Date to DateTime
    
    # First, add the old column back
    op.add_column('emf', sa.Column('creation_time', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    
    # Copy data from new column to old column (convert date to datetime)
    op.execute("UPDATE emf SET creation_time = creation_date::timestamp")
    
    # Drop the new column
    op.drop_column('emf', 'creation_date')
