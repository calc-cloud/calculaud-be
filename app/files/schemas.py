from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class FileAttachmentBase(BaseModel):
    original_filename: Annotated[str, Field(max_length=255)]
    mime_type: Annotated[str, Field(max_length=100)]
    file_size: int


class FileAttachment(FileAttachmentBase):
    id: int
    s3_key: str
    uploaded_at: datetime
    purpose_id: int | None

    model_config = ConfigDict(from_attributes=True)


class FileUploadResponse(BaseModel):
    file_id: int
    original_filename: str
    mime_type: str
    file_size: int
    uploaded_at: datetime
    message: str = "File uploaded successfully"


class FileDownloadResponse(BaseModel):
    file_id: int
    original_filename: str
    download_url: str
    expires_in: int  # seconds
