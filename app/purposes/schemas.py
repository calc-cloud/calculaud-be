from datetime import date, datetime
from typing import Annotated, Literal

from fastapi.params import Query
from pydantic import BaseModel, ConfigDict, Field

from app import StatusEnum
from app.files.schemas import FileAttachmentResponse
from app.hierarchies.schemas import Hierarchy
from app.pagination import PaginationParams
from app.purchases.schemas import PurchaseResponse
from app.responsible_authorities.schemas import ResponsibleAuthorityResponse


class PurposeContentBase(BaseModel):
    service_id: Annotated[
        int,
        Field(
            description="ID of the service/item being procured (e.g., laptop, software license)"
        ),
    ]
    quantity: Annotated[
        int,
        Field(
            ge=1,
            description="Number of units to procure (minimum 1, e.g., 5 laptops, 10 licenses)",
        ),
    ]


class PurposeContentCreate(PurposeContentBase):
    pass


class PurposeContentUpdate(PurposeContentBase):
    pass


class PurposeContent(PurposeContentBase):
    """Service item within a procurement purpose with resolved names for display."""

    id: int
    service_name: Annotated[
        str,
        Field(
            description="Display name of the service (e.g., 'Dell Laptop XPS 13', 'Office 365 License')"
        ),
    ]
    service_type: Annotated[
        str,
        Field(
            description="Category of the service (e.g., 'IT Equipment', 'Software', 'Office Supplies')"
        ),
    ]

    model_config = ConfigDict(from_attributes=True)


class PurposeBase(BaseModel):
    expected_delivery: Annotated[
        date | None,
        Field(
            default=None,
            description="Expected delivery date for the procurement (YYYY-MM-DD format, e.g., 2024-12-31)",
        ),
    ]
    comments: Annotated[
        str | None,
        Field(
            default=None,
            max_length=1000,
            description="Additional notes or special instructions (max 1000 chars, e.g., 'Urgent for Q4 project')",
        ),
    ]
    status: Annotated[
        StatusEnum,
        Field(
            default=StatusEnum.IN_PROGRESS,
            description="Current workflow status: IN_PROGRESS (active), COMPLETED (ready for approval), SIGNED (approved), PARTIALLY_SUPPLIED (partial delivery)",
        ),
    ]
    supplier_id: Annotated[
        int | None,
        Field(
            default=None,
            description="ID of preferred or selected supplier (optional, can be assigned later in workflow)",
        ),
    ]
    description: Annotated[
        str | None,
        Field(
            default=None,
            max_length=2000,
            description="Detailed description of what's being procured (max 2000 chars, e.g., 'Development team laptops for new hires')",
        ),
    ]
    service_type_id: Annotated[
        int | None,
        Field(
            default=None,
            description="ID of primary service type category (e.g., IT Equipment=1, Software=2, Office Supplies=3)",
        ),
    ]


class PurposeCreate(PurposeBase):
    hierarchy_id: Annotated[
        int | None,
        Field(
            default=None,
            description="ID of organizational hierarchy (department/unit) responsible for this procurement",
        ),
    ]
    file_attachment_ids: Annotated[
        list[int],
        Field(
            default_factory=list,
            description="List of pre-uploaded file IDs to attach (upload files first, then reference IDs here)",
        ),
    ]
    contents: Annotated[
        list[PurposeContentCreate],
        Field(
            default_factory=list,
            description="List of services/items to procure with quantities (e.g., [{'service_id': 1, 'quantity': 5}])",
        ),
    ]


class PurposeUpdate(BaseModel):
    hierarchy_id: Annotated[int | None, Field(default=None)]
    expected_delivery: Annotated[date | None, Field(default=None)]
    comments: Annotated[str | None, Field(default=None, max_length=1000)]
    status: Annotated[StatusEnum | None, Field(default=None)]
    supplier_id: int | None = None
    service_type_id: int | None = None
    description: Annotated[str | None, Field(default=None, max_length=2000)]
    file_attachment_ids: Annotated[list[int] | None, Field(default=None)]
    contents: Annotated[list[PurposeContentUpdate] | None, Field(default=None)]


class Purpose(PurposeBase):
    """
    Complete procurement purpose with all related data and computed fields.

    This is the primary entity representing a procurement request with full workflow,
    financial, and organizational context.
    """

    id: Annotated[int, Field(description="Unique purpose identifier")]
    creation_time: Annotated[
        datetime,
        Field(description="When the purpose was initially created (ISO format)"),
    ]
    last_modified: Annotated[
        datetime,
        Field(
            description="Last update timestamp, automatically updated when any related data changes"
        ),
    ]

    # Resolved display names (computed from IDs)
    supplier: Annotated[
        str | None,
        Field(
            description="Supplier company name (resolved from supplier_id, e.g., 'Dell Technologies')"
        ),
    ] = None
    service_type: Annotated[
        str | None,
        Field(
            description="Primary service category name (resolved from service_type_id, e.g., 'IT Equipment')"
        ),
    ] = None

    # Related objects with full details
    hierarchy: Annotated[
        Hierarchy | None,
        Field(
            description="Complete organizational hierarchy details (department, unit, path)"
        ),
    ] = None
    pending_authority: Annotated[
        ResponsibleAuthorityResponse | None,
        Field(
            description="Person responsible for the next workflow approval (computed from current incomplete stages)"
        ),
    ] = None

    # Collections of related data
    file_attachments: Annotated[
        list[FileAttachmentResponse],
        Field(
            default_factory=list,
            description="Attached documents (quotes, specifications, approvals)",
        ),
    ]
    contents: Annotated[
        list[PurposeContent],
        Field(
            default_factory=list,
            description="Specific services/items being procured with quantities and resolved names",
        ),
    ]
    purchases: Annotated[
        list[PurchaseResponse],
        Field(
            default_factory=list,
            description="Purchase workflows with stages, costs, and approval chain progress",
        ),
    ]

    model_config = ConfigDict(from_attributes=True)


class FilterParams(BaseModel):
    """
    Universal filter parameters for analytics and purpose queries.

    All filters work together (AND logic) to narrow results. Use multiple filters
    to create precise queries like "IT equipment from last quarter awaiting approval".
    """

    start_date: Annotated[
        date | None,
        Query(
            default=None,
            description="Filter by purpose creation date from (inclusive, YYYY-MM-DD format, e.g., 2024-01-01)",
        ),
    ]
    end_date: Annotated[
        date | None,
        Query(
            default=None,
            description="Filter by purpose creation date to (inclusive, YYYY-MM-DD format, e.g., 2024-12-31)",
        ),
    ]
    service_ids: Annotated[
        list[int] | None,
        Query(
            default=None,
            description="Filter by specific service/item IDs (e.g., [1, 5, 12] for specific laptops, software)",
            alias="service_id",
        ),
    ]
    service_type_ids: Annotated[
        list[int] | None,
        Query(
            default=None,
            description="Filter by service category IDs (e.g., [1] for IT Equipment, [2] for Software)",
            alias="service_type_id",
        ),
    ]
    hierarchy_ids: Annotated[
        list[int] | None,
        Query(
            default=None,
            description="Filter by organizational hierarchy IDs - includes ALL child hierarchies (e.g., [5] includes unit and all departments)",
            alias="hierarchy_id",
        ),
    ]
    statuses: Annotated[
        list[StatusEnum] | None,
        Query(
            default=None,
            description="Filter by workflow status (e.g., ['IN_PROGRESS'] for active, ['COMPLETED', 'SIGNED'] for finished)",
            alias="status",
        ),
    ]
    supplier_ids: Annotated[
        list[int] | None,
        Query(
            default=None,
            description="Filter by supplier company IDs (e.g., [3, 7] for Dell and Microsoft purchases)",
            alias="supplier_id",
        ),
    ]
    pending_authorities: Annotated[
        list[int] | None,
        Query(
            default=None,
            description="Filter by responsible authority IDs - shows purposes waiting for specific people's approval (e.g., [12] for John's pending items)",
            alias="pending_authority_id",
        ),
    ]


class GetPurposesRequest(FilterParams, PaginationParams):
    """
    Complete request parameters for searching and filtering procurement purposes.

    Combines filtering, searching, sorting, and pagination for comprehensive purpose queries.
    Perfect for complex requests like "Show me IT equipment over $5k from Q3, sorted by urgency".
    """

    search: Annotated[
        str | None,
        Field(
            default=None,
            description="Free-text search across purpose descriptions, stage values, and service names (e.g., 'laptop', 'urgent', 'development team')",
        ),
    ]
    sort_by: Annotated[
        str,
        Field(
            default="creation_time",
            description="Sort by field: creation_time (when created), last_modified (latest update), expected_delivery (deadline), days_since_last_completion (workflow delays)",
        ),
    ]
    sort_order: Annotated[
        Literal["asc", "desc"],
        Field(
            default="desc",
            description="Sort order: 'desc' (newest/highest first), 'asc' (oldest/lowest first)",
        ),
    ]
