from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi import status as statuses
from sqlalchemy.orm import Session

from app.database import get_db
from app.files import service
from app.files.exceptions import FileNotFoundError, FileUploadError
from app.files.schemas import FileDownloadResponse, FileUploadResponse

router = APIRouter()


@router.post(
    "/upload", response_model=FileUploadResponse, status_code=statuses.HTTP_201_CREATED
)
def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a file to S3 and save metadata."""
    if not file.filename:
        raise HTTPException(
            status_code=statuses.HTTP_400_BAD_REQUEST, detail="No file provided"
        )

    try:
        return service.upload_file(
            db=db,
            file_obj=file.file,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
        )
    except FileUploadError as e:
        raise HTTPException(
            status_code=statuses.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{file_id}", response_model=FileDownloadResponse)
def get_file_download_url(
    file_id: int,
    db: Session = Depends(get_db),
):
    """Get presigned download URL for a file."""
    try:
        return service.get_file_download_url(db=db, file_id=file_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=statuses.HTTP_404_NOT_FOUND, detail=str(e))
    except FileUploadError as e:
        raise HTTPException(
            status_code=statuses.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.delete("/{file_id}", status_code=statuses.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
):
    """Delete a file from S3 and database."""
    try:
        service.delete_file(db=db, file_id=file_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=statuses.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=statuses.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
