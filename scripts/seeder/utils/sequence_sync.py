"""Database sequence synchronization utilities."""

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session


def sync_postgresql_sequences(session: Session) -> None:
    """
    Synchronize PostgreSQL sequences after inserting records with explicit IDs.

    This is necessary when seeding reference data with specific IDs to ensure
    auto-increment sequences are properly updated.

    Args:
        session: Database session
    """
    try:
        print("    Synchronizing database sequences...")

        # Table -> sequence mappings for tables that use explicit IDs
        sequence_mappings = {
            "hierarchy": "hierarchy_id_seq",
            "stage_type": "stage_type_id_seq",
            "predefined_flow": "predefined_flow_id_seq",
            "responsible_authority": "responsible_authority_id_seq",
            "budget_source": "budget_source_id_seq",
        }

        for table_name, sequence_name in sequence_mappings.items():
            try:
                # Check if table has any records
                result = session.execute(
                    text(f"SELECT MAX(id) FROM {table_name}")
                ).scalar()

                if result is not None:
                    # Sync the sequence to the max ID
                    session.execute(text(f"SELECT setval('{sequence_name}', {result})"))
                    print(f"    Synchronized {sequence_name} to {result}")
                else:
                    print(
                        f"      No records found in {table_name}, skipping {sequence_name}"
                    )

            except OperationalError as e:
                # Sequence or table might not exist
                print(f"      Could not sync {sequence_name}: {e}")
                continue

        print("    Database sequences synchronized")

    except Exception as e:
        print(f"      Warning: Could not sync sequences: {e}")
        # Don't raise - this is not critical for SQLite or if sequences don't exist


def check_sequence_consistency(session: Session) -> dict[str, dict[str, int]]:
    """
    Check consistency between table max IDs and sequence current values.

    Args:
        session: Database session

    Returns:
        Dictionary with consistency check results
    """
    results = {}

    sequence_mappings = {
        "hierarchy": "hierarchy_id_seq",
        "stage_type": "stage_type_id_seq",
        "predefined_flow": "predefined_flow_id_seq",
        "responsible_authority": "responsible_authority_id_seq",
        "budget_source": "budget_source_id_seq",
    }

    for table_name, sequence_name in sequence_mappings.items():
        try:
            # Get max ID from table
            max_id_result = session.execute(
                text(f"SELECT MAX(id) FROM {table_name}")
            ).scalar()
            max_id = max_id_result if max_id_result is not None else 0

            # Get current sequence value
            seq_value_result = session.execute(
                text(f"SELECT last_value FROM {sequence_name}")
            ).scalar()
            seq_value = seq_value_result if seq_value_result is not None else 0

            results[table_name] = {
                "max_id": max_id,
                "sequence_value": seq_value,
                "consistent": max_id <= seq_value,
            }

        except OperationalError:
            # Table or sequence doesn't exist
            results[table_name] = {
                "max_id": 0,
                "sequence_value": 0,
                "consistent": True,
                "note": "Table or sequence not found",
            }

    return results


def fix_sequence_inconsistencies(session: Session) -> None:
    """
    Automatically fix any sequence inconsistencies found.

    Args:
        session: Database session
    """
    consistency_check = check_sequence_consistency(session)

    print("    Checking sequence consistency...")

    inconsistent_found = False
    for table_name, info in consistency_check.items():
        if not info["consistent"] and "note" not in info:
            inconsistent_found = True
            print(
                f"      {table_name}: max_id={info['max_id']}, sequence={info['sequence_value']}"
            )

    if inconsistent_found:
        print("    Fixing sequence inconsistencies...")
        sync_postgresql_sequences(session)
    else:
        print("    All sequences are consistent")


class SequenceManager:
    """Context manager for handling sequence synchronization during seeding."""

    def __init__(self, session: Session, sync_on_exit: bool = True):
        """
        Initialize the sequence manager.

        Args:
            session: Database session
            sync_on_exit: Whether to sync sequences when exiting context
        """
        self.session = session
        self.sync_on_exit = sync_on_exit

    def __enter__(self):
        """Enter the context - check initial sequence state."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context - sync sequences if requested."""
        if self.sync_on_exit and exc_type is None:
            # Only sync if no exception occurred
            sync_postgresql_sequences(self.session)
