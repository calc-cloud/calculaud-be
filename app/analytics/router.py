from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.params import Query
from sqlalchemy.orm import Session

from app.analytics.schemas import (
    ExpenditureTimelineRequest,
    HierarchyDistributionRequest,
    HierarchyDistributionResponse,
    ServicesQuantityResponse,
    ServiceTypesDistributionResponse,
    TimelineExpenditureResponse,
)
from app.analytics.service import AnalyticsService
from app.database import get_db
from app.purposes.schemas import FilterParams

router = APIRouter()


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency to get analytics service."""
    return AnalyticsService(db)


@router.get(
    "/services/quantities",
    response_model=ServicesQuantityResponse,
    operation_id="get_services_quantities",
)
def get_services_quantities(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    filters: Annotated[FilterParams, Query()],
) -> ServicesQuantityResponse:
    """
    Calculate total quantities procured for each service/item type.

    🎯 **Use Cases:**
    - Inventory planning: "How many laptops did we order this year?"
    - Volume analysis: "Which services have highest procurement volumes?"
    - Resource allocation: "Show quantities by department for budget planning"
    - Trend analysis: "Compare service quantities quarter over quarter"

    📊 **Returns:** List of services with:
    - id: Service identifier
    - name: Service name (e.g., "Dell Laptop XPS 13", "Office 365 License")
    - service_type_id: Service type identifier
    - service_type_name: Category name (e.g., "Application Development", "Cloud Infrastructure")
    - quantity: Total units procured across all filtered purposes

    💡 **Examples:**
    - "Show all IT equipment quantities this year" → filter by service_type_id + date range
    - "How many licenses purchased by development team?" → filter by hierarchy_id + service search

    📈 **Perfect for:** Bar charts showing procurement volumes, inventory dashboards
    """
    return analytics_service.get_services_quantities(filters)


@router.get(
    "/service-types/distribution",
    response_model=ServiceTypesDistributionResponse,
    operation_id="get_service_types_distribution",
)
def get_service_types_distribution(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    filters: Annotated[FilterParams, Query()],
) -> ServiceTypesDistributionResponse:
    """
    Analyze distribution of procurement purposes across service type categories.

    🎯 **Use Cases:**
    - Budget allocation: "What percentage goes to IT vs Office Supplies?"
    - Category analysis: "Which service types generate most procurement requests?"
    - Compliance reporting: "Show procurement distribution by category for audit"
    - Strategic planning: "Identify dominant procurement categories by department"

    📊 **Returns:** List of service types with:
    - id: Service type identifier
    - name: Service type name (e.g., "Application Development", "Cloud Infrastructure", "Database Services")
    - count: Number of procurement purposes in this category

    💡 **Examples:**
    - "Show breakdown by Application Development vs Cloud Infrastructure"
    - "Which service types does the DevOps team procure most?"
    - "Compare Database Services vs Storage Solutions procurement volumes"

    🥧 **Perfect for:** Pie charts, donut charts showing category distributions
    """
    return analytics_service.get_service_types_distribution(filters)


@router.get(
    "/expenditure/timeline",
    response_model=TimelineExpenditureResponse,
    operation_id="get_expenditure_timeline",
)
def get_expenditure_timeline(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    request: Annotated[ExpenditureTimelineRequest, Query()],
) -> TimelineExpenditureResponse:
    """
    Analyze expenditure trends over time with multi-currency and service type breakdown.

    🎯 **Use Cases:**
    - Budget monitoring: "Show monthly spending trends this fiscal year"
    - Seasonal analysis: "Identify spending patterns by quarter"
    - Service category trends: "How has IT spending changed over time vs Office Supplies?"
    - Currency analysis: "Track USD vs ILS expenditure trends"
    - Variance reporting: "Compare actual spending timeline to budget"

    📊 **Returns:** Timeline data with:
    - time_period: Grouped period (e.g., "2024-01" for month, "2024-W12" for week)
    - total_ils: Total spending in Israeli Shekels for the period
    - total_usd: Total spending in USD equivalent for the period
    - data: Array of service types with individual expenditure breakdowns

    ⚙️ **Grouping Options:**
    - day: Daily expenditure (detailed short-term analysis)
    - week: Weekly expenditure (operational monitoring)
    - month: Monthly expenditure (standard business reporting)
    - year: Annual expenditure (strategic long-term trends)

    💰 **Currency Handling:**
    - Automatic conversion between ILS, SUPPORT_USD, and AVAILABLE_USD
    - Uses configurable exchange rates for accurate totals
    - Separate totals in both currencies for flexibility

    📈 **Perfect for:** Line charts, stacked area charts showing spending evolution
    """
    return analytics_service.get_expenditure_timeline(request, request)


@router.get(
    "/hierarchies/distribution",
    response_model=HierarchyDistributionResponse,
    operation_id="get_hierarchy_distribution",
)
def get_hierarchy_distribution(
    analytics_service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    request: Annotated[HierarchyDistributionRequest, Query()],
) -> HierarchyDistributionResponse:
    """
    Analyze procurement purpose distribution across organizational hierarchy with drill-down navigation.

    🎯 **Use Cases:**
    - Organizational analysis: "Which units generate most procurement requests?"
    - Budget allocation: "Show procurement distribution by department"
    - Management reporting: "Compare activity across centers and divisions"
    - Resource planning: "Identify high-procurement departments for staff allocation"
    - Drill-down investigation: "Start at unit level, drill down to specific teams"

    📊 **Returns:** List of hierarchy entities with:
    - id: Hierarchy identifier
    - name: Organization name (e.g., "IT Unit", "Development Center", "Backend Team")
    - type: Hierarchy level (UNIT, CENTER, ANAF, MADOR, TEAM)
    - parent_id: Parent hierarchy ID (for navigation and breadcrumb display)
    - path: Full organizational path for context
    - count: Total procurement purposes (includes ALL child hierarchies)

    🔍 **Navigation Modes:**
    1. **Top Level**: No parameters → shows all UNITs
    2. **Specific Level**: level=CENTER → shows all centers
    3. **Drill Down**: parent_id=5 → shows direct children of hierarchy #5
    4. **Level + Parent**: parent_id=5&level=TEAM → shows all teams under parent #5

    📈 **Hierarchy Chain:** UNIT (highest) → CENTER → ANAF → MADOR → TEAM (lowest)

    💡 **Examples:**
    - "Show procurement by top-level units" → no parameters
    - "Drill into IT Unit departments" → parent_id=3
    - "Show all teams under Development Center" → parent_id=7&level=TEAM

    🥧 **Perfect for:** Interactive hierarchical charts, org-tree visualizations with drill-down
    """
    return analytics_service.get_hierarchy_distribution(request, request)
