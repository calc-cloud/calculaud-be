#!/usr/bin/env python3
"""
Auto-flag stuck purposes script.

This script identifies purposes that have been stuck in stages for more than 10 days
and automatically flags them by setting is_flagged = True.

A purpose is considered "stuck" when:
- days_since_last_completion > 10 days
- status is not COMPLETED
- is_flagged is currently False (to avoid duplicate flagging)

Usage:
    python scripts/auto_flag_stuck_purposes.py
"""

import os
import sys
from datetime import datetime

# Add app to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import and_, create_engine, select, update
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.purposes.models import Purpose, StatusEnum
from app.purposes.sorting import build_days_since_last_completion_subquery


def create_db_session():
    """Create database session with same config as main app."""
    engine = create_engine(
        settings.database_url,
        connect_args=(
            {"check_same_thread": False}
            if settings.database_url.startswith("sqlite")
            else {}
        ),
        echo=settings.debug,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def main():
    """Main function to auto-flag stuck purposes."""
    print(f"{datetime.now()} - Starting auto-flag process")

    try:
        db = create_db_session()

        try:
            days_subquery = build_days_since_last_completion_subquery()
            update_stmt = (
                update(Purpose)
                .where(
                    and_(
                        Purpose.id.in_(
                            select(days_subquery.c.purpose_id).where(
                                and_(
                                    days_subquery.c.days_since_last_completion > 10,
                                    days_subquery.c.days_since_last_completion.is_not(
                                        None
                                    ),
                                )
                            )
                        ),
                        Purpose.status != StatusEnum.COMPLETED,
                        Purpose.is_flagged == False,  # Only unflagged ones
                    )
                )
                .values(is_flagged=True)
            )

            result = db.execute(update_stmt)
            db.commit()

            flagged_count = result.rowcount
            print(f"{datetime.now()} - Successfully flagged {flagged_count} purposes")

        finally:
            db.close()

    except Exception as e:
        print(f"{datetime.now()} - Error during auto-flag process: {str(e)}")
        sys.exit(1)

    print(f"{datetime.now()} - Auto-flag process completed")


if __name__ == "__main__":
    main()
