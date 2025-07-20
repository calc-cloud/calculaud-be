from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi import status as statuses
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.files.exceptions import FileNotFoundError, FileUploadError
from app.files.schemas import FileAttachmentResponse
from app.pagination import PaginatedResult, create_paginated_result
from app.purposes import service
from app.purposes.csv_export import export_purposes_csv
from app.purposes.file_service import delete_file_from_purpose, upload_file_to_purpose
from app.purposes.exceptions import (
    DuplicateServiceInPurpose,
    FileAttachmentsNotFound,
    FileNotAttachedToPurpose,
    PurposeNotFound,
    ServiceNotFound,
)
from app.purposes.schemas import (
    GetPurposesRequest,
    Purpose,
    PurposeCreate,
    PurposeUpdate,
)

router = APIRouter()


@router.get("/", response_model=PaginatedResult[Purpose])
def get_purposes(
    params: Annotated[GetPurposesRequest, Query()],
    db: Session = Depends(get_db),
):
    """Get all purposes with filtering, searching, sorting, and pagination."""
    purposes, total = service.get_purposes(
        db=db,
        params=params,
    )

    return create_paginated_result(purposes, total, params)


@router.get("/export_csv")
def export_csv(
    params: Annotated[GetPurposesRequest, Query()],
    db: Session = Depends(get_db),
):
    """Export all purposes as CSV with the same filtering, searching, and sorting as get_purposes."""
    csv_content = export_purposes_csv(db=db, params=params)
    
    # Generate filename with current date
    current_date = datetime.now().strftime("%d-%m-%Y")
    filename = f"purposes_export_{current_date}.csv"
    
    # Create streaming response for CSV download
    response = StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
    return response


@router.get("/{purpose_id}", response_model=Purpose)
def get_purpose(purpose_id: int, db: Session = Depends(get_db)):
    """Get a specific purpose by ID."""
    purpose = service.get_purpose(db, purpose_id)
    if not purpose:
        raise HTTPException(
            status_code=statuses.HTTP_404_NOT_FOUND, detail="Purpose not found"
        )
    return purpose


@router.post("/", response_model=Purpose, status_code=statuses.HTTP_201_CREATED)
def create_purpose(purpose: PurposeCreate, db: Session = Depends(get_db)):
    """Create a new purpose."""
    try:
        return service.create_purpose(db, purpose)
    except (
        ServiceNotFound,
        DuplicateServiceInPurpose,
        FileAttachmentsNotFound,
    ) as e:
        raise HTTPException(status_code=statuses.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{purpose_id}", response_model=Purpose)
def patch_purpose(
    purpose_id: int, purpose_update: PurposeUpdate, db: Session = Depends(get_db)
):
    """Patch an existing purpose."""
    try:
        patched_purpose = service.patch_purpose(db, purpose_id, purpose_update)
        if not patched_purpose:
            raise HTTPException(
                status_code=statuses.HTTP_404_NOT_FOUND, detail="Purpose not found"
            )
        return patched_purpose
    except (
        ServiceNotFound,
        DuplicateServiceInPurpose,
        FileAttachmentsNotFound,
    ) as e:
        raise HTTPException(status_code=statuses.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{purpose_id}", status_code=statuses.HTTP_204_NO_CONTENT)
def delete_purpose(purpose_id: int, db: Session = Depends(get_db)):
    """Delete a purpose."""
    if not service.delete_purpose(db, purpose_id):
        raise HTTPException(
            status_code=statuses.HTTP_404_NOT_FOUND, detail="Purpose not found"
        )


@router.post(
    "/{purpose_id}/files",
    response_model=FileAttachmentResponse,
    status_code=statuses.HTTP_201_CREATED,
)
def upload_file(
    purpose_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a file and attach it to a specific purpose."""
    if not file.filename:
        raise HTTPException(
            status_code=statuses.HTTP_400_BAD_REQUEST, detail="No file provided"
        )

    try:
        return upload_file_to_purpose(
            db=db,
            purpose_id=purpose_id,
            file_obj=file.file,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
        )
    except PurposeNotFound as e:
        raise HTTPException(status_code=statuses.HTTP_404_NOT_FOUND, detail=str(e))
    except FileUploadError as e:
        raise HTTPException(
            status_code=statuses.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete(
    "/{purpose_id}/files/{file_id}", status_code=statuses.HTTP_204_NO_CONTENT
)
def delete_file(
    purpose_id: int,
    file_id: int,
    db: Session = Depends(get_db),
):
    """Remove a file from a purpose and delete the file entirely."""
    try:
        delete_file_from_purpose(db, purpose_id, file_id)
    except PurposeNotFound as e:
        raise HTTPException(status_code=statuses.HTTP_404_NOT_FOUND, detail=str(e))
    except FileNotAttachedToPurpose as e:
        raise HTTPException(status_code=statuses.HTTP_404_NOT_FOUND, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=statuses.HTTP_404_NOT_FOUND, detail=str(e))
