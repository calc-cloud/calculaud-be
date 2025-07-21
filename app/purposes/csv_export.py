import csv
import io

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app import Purchase
from app.purchases.schemas import PurchaseResponse
from app.purposes.filters import apply_filters
from app.purposes.models import Purpose, PurposeContent
from app.purposes.schemas import GetPurposesRequest
from app.purposes.service import build_search_filter, get_base_purpose_select

# Stage type name constants
EMF_ID_STAGE_NAME = "emf_id"
BIKUSHIT_ID_STAGE_NAME = "bikushit_id"
DEMAND_ID_STAGE_NAME = "demand_id"
ORDER_ID_STAGE_NAME = "order_id"


def get_purposes_for_export(db: Session, params: GetPurposesRequest) -> list[Purpose]:
    """Get all purposes for CSV export with proper filtering and sorting."""
    stmt = get_base_purpose_select()

    # Apply universal filters using the centralized filtering method
    stmt = apply_filters(stmt, params, db)

    # Apply search
    if params.search:
        search_filter = build_search_filter(params.search)
        stmt = stmt.where(search_filter)

    # Apply sorting
    sort_column = getattr(Purpose, params.sort_by, Purpose.creation_time)
    if params.sort_order == "desc":
        stmt = stmt.order_by(desc(sort_column))
    else:
        stmt = stmt.order_by(sort_column)

    # Execute query without pagination to get all results
    return list(db.execute(stmt).unique().scalars().all())


def get_csv_headers() -> list[str]:
    """Return the CSV column headers."""
    return [
        "ID",
        "Description",
        "Status",
        "Creation Time",
        "Last Modified",
        "Expected Delivery",
        "Comments",
        "Hierarchy",
        "Supplier",
        "Service Type",
        "Services",
        "Purchases",
        "EMF IDs",
        "EMF IDs Completion Date",
        "Bikushit IDs",
        "Bikushit IDs Completion Date",
        "Demand IDs",
        "Demand IDs Completion Date",
        "Order IDs",
        "Order IDs Completion Date",
        "Pending Stages",
        "File Attachments",
    ]


def extract_purchase_stage_data(purchase: Purchase) -> dict[str, str]:
    """Extract stage IDs and completion dates from a single purchase."""
    # Create a dictionary for quick stage lookup by stage type name
    stage_dict = {
        stage.stage_type.name: stage
        for stage in purchase.stages
        if stage.value  # Only include stages with values
    }

    emf_stage = stage_dict.get(EMF_ID_STAGE_NAME)
    bikushit_stage = stage_dict.get(BIKUSHIT_ID_STAGE_NAME)
    demand_stage = stage_dict.get(DEMAND_ID_STAGE_NAME)
    order_stage = stage_dict.get(ORDER_ID_STAGE_NAME)

    return {
        "emf_id": emf_stage.value or "" if emf_stage else "",
        "emf_completion_date": (
            emf_stage.completion_date.isoformat()
            if emf_stage and emf_stage.completion_date
            else ""
        ),
        "bikushit_id": bikushit_stage.value or "" if bikushit_stage else "",
        "bikushit_completion_date": (
            bikushit_stage.completion_date.isoformat()
            if bikushit_stage and bikushit_stage.completion_date
            else ""
        ),
        "demand_id": demand_stage.value or "" if demand_stage else "",
        "demand_completion_date": (
            demand_stage.completion_date.isoformat()
            if demand_stage and demand_stage.completion_date
            else ""
        ),
        "order_id": order_stage.value or "" if order_stage else "",
        "order_completion_date": (
            order_stage.completion_date.isoformat()
            if order_stage and order_stage.completion_date
            else ""
        ),
    }


def format_purchase_stages_for_csv(purposes: list[Purpose]) -> dict[int, dict]:
    """Format all stage data for all purchases organized by purpose_id."""
    stage_data = {}

    for purpose in purposes:
        # Extract IDs and completion dates from purchases stages, maintaining purchase order and relationship
        emf_ids = []
        emf_completion_dates = []
        bikushit_ids = []
        bikushit_completion_dates = []
        demand_ids = []
        demand_completion_dates = []
        order_ids = []
        order_completion_dates = []

        # Process purchases in order to maintain relationships between IDs and completion dates
        for purchase in purpose.purchases:
            purchase_stage_data = extract_purchase_stage_data(purchase)

            # Only add entries if at least one ID exists for this purchase
            if any(
                [
                    purchase_stage_data["emf_id"],
                    purchase_stage_data["bikushit_id"],
                    purchase_stage_data["demand_id"],
                    purchase_stage_data["order_id"],
                ]
            ):
                emf_ids.append(purchase_stage_data["emf_id"])
                emf_completion_dates.append(purchase_stage_data["emf_completion_date"])
                bikushit_ids.append(purchase_stage_data["bikushit_id"])
                bikushit_completion_dates.append(
                    purchase_stage_data["bikushit_completion_date"]
                )
                demand_ids.append(purchase_stage_data["demand_id"])
                demand_completion_dates.append(
                    purchase_stage_data["demand_completion_date"]
                )
                order_ids.append(purchase_stage_data["order_id"])
                order_completion_dates.append(
                    purchase_stage_data["order_completion_date"]
                )

        # Join IDs and completion dates with newlines (each on its own line, maintaining purchase order)
        stage_data[purpose.id] = {
            "emf_ids_str": "\n".join(emf_ids),
            "emf_completion_dates_str": "\n".join(emf_completion_dates),
            "bikushit_ids_str": "\n".join(bikushit_ids),
            "bikushit_completion_dates_str": "\n".join(bikushit_completion_dates),
            "demand_ids_str": "\n".join(demand_ids),
            "demand_completion_dates_str": "\n".join(demand_completion_dates),
            "order_ids_str": "\n".join(order_ids),
            "order_completion_dates_str": "\n".join(order_completion_dates),
        }

    return stage_data


def calculate_pending_stages_info(purchase: Purchase) -> str:
    """Calculate pending stages string for a purchase."""
    # Use existing computed fields from Purchase model properties
    purchase_response = PurchaseResponse.model_validate(purchase)

    current_pending_stages = purchase_response.current_pending_stages
    days_since_last_completion = purchase_response.days_since_last_completion

    if not current_pending_stages or days_since_last_completion is None:
        return ""

    # Format pending stages names
    pending_stage_names = [stage.stage_type.name for stage in current_pending_stages]
    return f"{days_since_last_completion} days in {', '.join(pending_stage_names)}"


def format_services_list(purpose_contents: list[PurposeContent]) -> str:
    """Format purpose contents into services string."""
    return "\n".join(
        [f"{content.quantity} {content.service_name}" for content in purpose_contents]
    )


def get_file_attachments_info(purpose: Purpose) -> str:
    """Get file attachment names for a purpose."""
    return "\n".join([file.original_filename for file in purpose.file_attachments])


def build_csv_row_for_purpose(
    purpose: Purpose, stage_data: dict, pending_stages_data: dict
) -> list[str]:
    """Build a single CSV row for a purpose."""
    # Get purchase IDs (each on its own line)
    purchase_ids = [str(purchase.id) for purchase in purpose.purchases]
    purchase_ids_str = "\n".join(purchase_ids)

    # Get pre-calculated data
    purpose_stage_data = stage_data.get(purpose.id, {})
    pending_stages_str = pending_stages_data.get(purpose.id, "")

    # Format other data
    services = format_services_list(purpose.contents)
    file_attachments = get_file_attachments_info(purpose)

    return [
        str(purpose.id),
        purpose.description or "",
        purpose.status.value if purpose.status else "",
        purpose.creation_time.isoformat() if purpose.creation_time else "",
        purpose.last_modified.isoformat() if purpose.last_modified else "",
        purpose.expected_delivery.isoformat() if purpose.expected_delivery else "",
        purpose.comments or "",
        purpose.hierarchy.path if purpose.hierarchy else "",
        purpose.supplier or "",
        purpose.service_type or "",
        services,
        purchase_ids_str,
        purpose_stage_data.get("emf_ids_str", ""),
        purpose_stage_data.get("emf_completion_dates_str", ""),
        purpose_stage_data.get("bikushit_ids_str", ""),
        purpose_stage_data.get("bikushit_completion_dates_str", ""),
        purpose_stage_data.get("demand_ids_str", ""),
        purpose_stage_data.get("demand_completion_dates_str", ""),
        purpose_stage_data.get("order_ids_str", ""),
        purpose_stage_data.get("order_completion_dates_str", ""),
        pending_stages_str,
        file_attachments,
    ]


def build_all_csv_rows(
    purposes: list[Purpose], stage_data: dict, pending_stages_data: dict
) -> list[list[str]]:
    """Build CSV rows for all purposes."""
    return [
        build_csv_row_for_purpose(purpose, stage_data, pending_stages_data)
        for purpose in purposes
    ]


def generate_csv_string(headers: list[str], rows: list[list[str]]) -> str:
    """Convert headers and rows into CSV string."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)

    # Write header row
    writer.writerow(headers)

    # Write data rows
    for row in rows:
        writer.writerow(row)

    return output.getvalue()


def export_purposes_csv(db: Session, params: GetPurposesRequest) -> str:
    """
    Export purposes as CSV with filtering, searching, and sorting.
    Returns all purposes without pagination.
    """
    # 1. Get data
    purposes = get_purposes_for_export(db, params)

    # 2. Pre-process stage data
    stage_data = format_purchase_stages_for_csv(purposes)

    # 3. Pre-process pending stages
    pending_stages_data = {
        purpose.id: "\n".join(
            [calculate_pending_stages_info(purchase) for purchase in purpose.purchases]
        )
        for purpose in purposes
    }

    # 4. Build CSV
    headers = get_csv_headers()
    rows = build_all_csv_rows(purposes, stage_data, pending_stages_data)

    # 5. Generate CSV string
    return generate_csv_string(headers, rows)
