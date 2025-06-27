"""File-specific test fixtures."""

import uuid

import pytest

from app import FileAttachment


# File upload fixtures
@pytest.fixture
def sample_file_attachment(db_session) -> FileAttachment:
    """Create sample file attachment in database."""
    unique_key = str(uuid.uuid4())
    file_attachment = FileAttachment(
        original_filename="test.pdf",
        s3_key=f"files/test-{unique_key}.pdf",
        mime_type="application/pdf",
        file_size=1024,
    )
    db_session.add(file_attachment)
    db_session.commit()
    db_session.refresh(file_attachment)
    return file_attachment


@pytest.fixture
def multiple_file_attachments(db_session) -> list[FileAttachment]:
    """Create multiple sample file attachments in database."""
    files = [
        FileAttachment(
            original_filename="file1.pdf",
            s3_key=f"files/file1-{uuid.uuid4()}.pdf",
            mime_type="application/pdf",
            file_size=1024,
        ),
        FileAttachment(
            original_filename="file2.jpg",
            s3_key=f"files/file2-{uuid.uuid4()}.jpg",
            mime_type="image/jpeg",
            file_size=2048,
        ),
    ]
    db_session.add_all(files)
    db_session.commit()
    for file_attachment in files:
        db_session.refresh(file_attachment)
    return files
