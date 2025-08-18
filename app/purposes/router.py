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
from app.purposes.exceptions import (
    DuplicateServiceInPurpose,
    FileAttachmentsNotFound,
    FileNotAttachedToPurpose,
    PurposeNotFound,
    ServiceNotFound,
)
from app.purposes.file_service import delete_file_from_purpose, upload_file_to_purpose
from app.purposes.schemas import (
    GetPurposesRequest,
    Purpose,
    PurposeCreate,
    PurposeUpdate,
)

router = APIRouter()


@router.get("/", response_model=PaginatedResult[Purpose], operation_id="get_purposes")
def get_purposes(
    params: Annotated[GetPurposesRequest, Query()],
    db: Session = Depends(get_db),
):
    """
    Search and retrieve procurement purposes with comprehensive filtering and analysis.

    🎯 **Primary Use Cases:**
    - Search specific procurement requests: "Show me laptop purchases", "Find IT equipment"
    - Filter by workflow status: "Get all pending approvals", "Show completed purchases"
    - Organizational filtering: "IT department purchases", "Show purposes from Unit X"
    - Financial analysis: "High-value equipment over $10,000", "This quarter's expenses"
    - Timeline tracking: "Recent purchases needing attention", "Delayed approvals"
    - Authority management: "Show purposes waiting for John's approval"

    📊 **Returns:** Paginated list with full purpose details including:
    - Purchase workflow stages and current status
    - Cost breakdown by currency (ILS, USD)
    - File attachments and documentation
    - Organizational hierarchy and supplier information
    - Pending authority (who needs to act next on workflow)
    - Calculated fields like days since last completion

    💡 **Search Tips:**
    - Use 'search' for flexible text matching across descriptions, stage values, and services
    - Combine multiple filters for precise results (status + hierarchy + date range)
    - Sort by 'days_since_last_completion' to prioritize stalled purchases
    - Filter by 'pending_authority_id' to see what needs specific person's attention

    🔍 **Common Query Patterns:**
    - "Show me all IN_PROGRESS IT purchases from last month"
    - "Find expensive equipment waiting for approval"
    - "Get purposes with delays in their workflow"
    - "Show all purchases from supplier X this year"
    """
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
    """
    Export purposes to CSV file with full filtering capabilities.

    🎯 **Use Cases:**
    - Generate reports for management: "Export all IT purchases this quarter"
    - Compliance documentation: "Export all completed high-value purchases"
    - Data analysis: "Export purposes with delays for external analysis"
    - Audit preparation: "Export all purchases from specific suppliers"

    📋 **CSV Contents:** Complete purpose data including hierarchy, costs, stages, supplier info

    ⚡ **Performance:** Applies same filters as get_purposes but exports all matching results (no pagination)

    💾 **File Format:** Auto-generated filename with current date (purposes_export_DD-MM-YYYY.csv)
    """
    csv_content = export_purposes_csv(db=db, params=params)

    # Generate filename with current date
    current_date = datetime.now().strftime("%d-%m-%Y")
    filename = f"purposes_export_{current_date}.csv"

    # Create streaming response for CSV download
    response = StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
    return response


@router.get("/{purpose_id}", response_model=Purpose, operation_id="get_purpose")
def get_purpose(purpose_id: int, db: Session = Depends(get_db)):
    """
    Retrieve detailed information for a specific procurement purpose.

    🎯 **Use Cases:**
    - View complete purpose details: "Show me purpose #123"
    - Check workflow status: "What's the status of purchase ID 456?"
    - Review approval chain: "Who needs to approve purpose #789 next?"
    - Analyze purchase history: "Show full details of completed purchase"

    📊 **Returns:** Complete purpose with all related data:
    - Full workflow stages with completion dates and values
    - All costs by currency and purchase breakdown
    - File attachments and documentation
    - Current pending authority (next approver)
    - Organizational hierarchy and supplier details
    """
    purpose = service.get_purpose(db, purpose_id)
    if not purpose:
        raise HTTPException(
            status_code=statuses.HTTP_404_NOT_FOUND, detail="Purpose not found"
        )
    return purpose


@router.post("/", response_model=Purpose, status_code=statuses.HTTP_201_CREATED)
def create_purpose(purpose: PurposeCreate, db: Session = Depends(get_db)):
    """
    Create a new procurement purpose with services, hierarchy, and optional file attachments.

    🎯 **Use Cases:**
    - Initiate new procurement: "Create purchase request for laptops"
    - Start approval workflow: "Submit new equipment request to hierarchy"
    - Bulk service requests: "Create purpose with multiple service items"

    📋 **Required Data:**
    - Description of what's being procured
    - Services and quantities (what specifically to purchase)
    - Organizational hierarchy assignment
    - Optional: supplier, service type, file attachments

    ⚙️ **Business Logic:**
    - Validates unique services (no duplicates in same purpose)
    - Links file attachments by ID (must upload files first)
    - Sets default status to IN_PROGRESS
    - Triggers workflow creation if predefined flow exists
    """
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
    """
    Update an existing procurement purpose with partial data changes.

    🎯 **Use Cases:**
    - Update status: "Mark purpose as COMPLETED", "Change to SIGNED"
    - Modify details: "Update expected delivery date", "Add comments"
    - Change organization: "Reassign to different hierarchy", "Update supplier"
    - Manage services: "Add new service items", "Update quantities"
    - File management: "Attach additional documents", "Remove old files"

    ⚙️ **Update Behavior:**
    - Only provided fields are updated (partial updates)
    - Services list completely replaces existing (not merged)
    - File attachments list completely replaces existing
    - Automatically updates last_modified timestamp

    🔄 **Status Workflow:**
    - IN_PROGRESS → COMPLETED (when all stages done)
    - COMPLETED → SIGNED (management approval)
    - SIGNED → PARTIALLY_SUPPLIED (partial delivery)
    """
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
    """
    Permanently delete a procurement purpose and all related data.

    ⚠️ **WARNING:** This action cannot be undone and removes:
    - The purpose and all its content
    - All purchase records and workflow stages
    - All cost entries and financial data
    - File attachment links (files remain in storage)

    🎯 **Use Cases:**
    - Remove duplicate entries: "Delete accidentally created purpose"
    - Clean up test data: "Remove development test purposes"
    - Compliance cleanup: "Delete purposes per data retention policy"

    🔒 **Important:** Consider updating status instead of deletion for audit trails
    """
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
    """
    Upload and attach a document file to a specific procurement purpose.

    🎯 **Use Cases:**
    - Add supporting documents: "Attach vendor quote to purpose"
    - Include specifications: "Upload technical requirements document"
    - Compliance documentation: "Attach approval forms and certificates"
    - Reference materials: "Upload previous purchase records for comparison"

    📎 **Supported Files:** All common document formats (PDF, DOC, XLS, images, etc.)

    ☁️ **Storage:** Files uploaded to AWS S3 with automatic organization

    🔗 **Linking:** File automatically linked to the purpose for easy access
    """
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
    """
    Remove a file attachment from a purpose and delete it from storage.

    🎯 **Use Cases:**
    - Remove outdated documents: "Delete old vendor quote after update"
    - Clean up incorrect uploads: "Remove accidentally uploaded wrong file"
    - Manage document versions: "Delete superseded version of specification"

    ⚠️ **Complete Deletion:** File is removed from both the purpose and AWS S3 storage

    🔗 **Scope:** Only removes the file from this specific purpose (if shared, other links remain)
    """
    try:
        delete_file_from_purpose(db, purpose_id, file_id)
    except PurposeNotFound as e:
        raise HTTPException(status_code=statuses.HTTP_404_NOT_FOUND, detail=str(e))
    except FileNotAttachedToPurpose as e:
        raise HTTPException(status_code=statuses.HTTP_404_NOT_FOUND, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=statuses.HTTP_404_NOT_FOUND, detail=str(e))
