"""add_path_to_hierarchy

Revision ID: defbdc927e9c
Revises: 1f2729009357
Create Date: 2025-06-21 18:32:51.754784

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session


# revision identifiers, used by Alembic.
revision: str = 'defbdc927e9c'
down_revision: Union[str, Sequence[str], None] = '1f2729009357'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def calculate_path_for_hierarchy(session: Session, hierarchy_id: int, parent_id: int | None, name: str) -> str:
    """Calculate the full path for a hierarchy based on its parent."""
    if parent_id is None:
        return name
    
    parent = session.execute(
        sa.text("SELECT path FROM hierarchy WHERE id = :parent_id"),
        {"parent_id": parent_id}
    ).fetchone()
    
    if not parent or not parent[0]:
        return name
    
    return f"{parent[0]} / {name}" if parent[0] else name


def upgrade() -> None:
    """Upgrade schema."""
    # Add the path column
    op.add_column('hierarchy', sa.Column('path', sa.String(length=1000), nullable=True))
    
    # Get connection and session
    connection = op.get_bind()
    session = Session(bind=connection)
    
    try:
        # Get all hierarchies ordered by parent_id (roots first)
        hierarchies = session.execute(
            sa.text("SELECT id, parent_id, name FROM hierarchy ORDER BY parent_id NULLS FIRST")
        ).fetchall()
        
        # Calculate paths for each hierarchy
        for hierarchy in hierarchies:
            hierarchy_id, parent_id, name = hierarchy
            path = calculate_path_for_hierarchy(session, hierarchy_id, parent_id, name)
            
            # Update the path
            session.execute(
                sa.text("UPDATE hierarchy SET path = :path WHERE id = :id"),
                {"path": path, "id": hierarchy_id}
            )
        
        session.commit()
        
        # Make the column not nullable after populating data
        op.alter_column('hierarchy', 'path', nullable=False)
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('hierarchy', 'path')
