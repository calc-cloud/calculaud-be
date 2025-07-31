#!/usr/bin/env python3
"""
Database seeding script for creating stage types, predefined flows, and mock data.
Provides separate functions for base data setup and mock data generation.
"""

import argparse
import random
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.costs.models import Cost, CurrencyEnum
from app.database import Base
from app.hierarchies.models import Hierarchy, HierarchyTypeEnum
from app.predefined_flows.models import PredefinedFlow, PredefinedFlowStage
from app.purchases.models import Purchase
from app.purposes.models import Purpose, PurposeContent, StatusEnum
from app.service_types.models import ServiceType
from app.services.models import Service
from app.stage_types.models import StageType
from app.stages.models import Stage
from app.suppliers.models import Supplier

# Sample data - Cloud/IT focused
SERVICE_TYPES = [
    "Cloud Infrastructure",
    "Database Services",
    "Application Development",
    "DevOps & Automation",
    "Security & Monitoring",
    "Storage Solutions",
    "Network Services",
]

SERVICES_BY_TYPE = {
    "Cloud Infrastructure": [
        "AWS EC2 Instances",
        "Azure Virtual Machines",
        "Google Cloud Compute",
        "Load Balancers",
        "Auto Scaling Groups",
    ],
    "Database Services": [
        "PostgreSQL Hosting",
        "MySQL Management",
        "Redis Cache",
        "MongoDB Atlas",
        "Database Migration",
    ],
    "Application Development": [
        "API Development",
        "Microservices Architecture",
        "Container Orchestration",
        "Serverless Functions",
        "CI/CD Pipeline Setup",
    ],
    "DevOps & Automation": [
        "Infrastructure as Code",
        "Kubernetes Management",
        "Docker Container Registry",
        "Monitoring & Alerting",
        "Backup & Recovery",
    ],
    "Security & Monitoring": [
        "SSL Certificates",
        "Security Auditing",
        "Penetration Testing",
        "Log Analysis",
        "Compliance Monitoring",
    ],
    "Storage Solutions": [
        "AWS S3 Storage",
        "Azure Blob Storage",
        "CDN Services",
        "Data Archiving",
        "File System Management",
    ],
    "Network Services": [
        "VPN Setup",
        "DNS Management",
        "Firewall Configuration",
        "Network Monitoring",
        "Bandwidth Optimization",
    ],
}

SUPPLIERS = [
    "AWS Solutions",
    "Microsoft Azure",
    "Google Cloud Platform",
    "DigitalOcean",
    "CloudFlare",
    "MongoDB Inc",
    "Redis Labs",
    "Docker Enterprise",
    "HashiCorp",
    "GitLab Enterprise",
]


def get_existing_hierarchies(session: Any) -> list[int]:
    """Get existing hierarchy IDs from database."""
    hierarchies = session.query(Hierarchy).all()
    return [h.id for h in hierarchies]


def seed_hierarchies_from_backup(session: Any) -> list[int]:
    """Create hierarchies from backup data and return all hierarchy IDs."""
    hierarchy_ids = []

    # Hierarchy data from hierarchy_backup.sql
    hierarchy_data = [
        (1, None, "UNIT", "8000", "8000"),
        (2, 1, "CENTER", "7100", "8000 / 7100"),
        (3, 2, "ANAF", "810", "8000 / 7100 / 810"),
        (4, None, "UNIT", "9900", "9900"),
        (5, 4, "CENTER", "9910", "9900 / 9910"),
        (6, 3, "MADOR", "811", "8000 / 7100 / 810 / 811"),
        (7, 6, "TEAM", "Hero", "8000 / 7100 / 810 / 811 / Hero"),
        (8, 3, "TEAM", "צוות", "8000 / 7100 / 810 / צוות"),
        (9, 6, "TEAM", "YoYo", "8000 / 7100 / 810 / 811 / YoYo"),
        (10, 3, "MADOR", "815", "8000 / 7100 / 810 / 815"),
        (11, 10, "TEAM", "Loop", "8000 / 7100 / 810 / 815 / Loop"),
        (12, 3, "MADOR", "816", "8000 / 7100 / 810 / 816"),
        (13, 1, "CENTER", "5160", "8000 / 5160"),
        (14, 5, "ANAF", "450", "9900 / 9910 / 450"),
        (15, 4, "CENTER", "9930", "9900 / 9930"),
        (16, 14, "MADOR", "451", "9900 / 9910 / 450 / 451"),
        (17, 16, "TEAM", "Micky", "9900 / 9910 / 450 / 451 / Micky"),
        (18, 16, "TEAM", "Foody", "9900 / 9910 / 450 / 451 / Foody"),
        (19, 15, "TEAM", "Toto", "9900 / 9930 / Toto"),
        (20, 12, "TEAM", "Gorilla", "8000 / 7100 / 810 / 816 / Gorilla"),
        (21, 1, "CENTER", "Human Resources", "8000 / Human Resources"),
        (22, 2, "ANAF", "820", "8000 / 7100 / 820"),
        (24, 10, "TEAM", "Lamp", "8000 / 7100 / 810 / 815 / Lamp"),
        (25, 6, "TEAM", "Daddy", "8000 / 7100 / 810 / 811 / Daddy"),
        (26, 14, "MADOR", "459", "9900 / 9910 / 450 / 459"),
    ]

    # Create hierarchies with explicit IDs
    for hierarchy_id, parent_id, type_str, name, path in hierarchy_data:
        hierarchy = Hierarchy(
            id=hierarchy_id,
            parent_id=parent_id,
            type=HierarchyTypeEnum(type_str),
            name=name,
            path=path,
        )
        session.add(hierarchy)
        hierarchy_ids.append(hierarchy_id)

    session.flush()
    return hierarchy_ids


def seed_stage_types(session: Any) -> list[int]:
    """Create stage types from backup data and return their IDs."""
    stage_type_ids = []

    # Stage type data from stage_type_backup.sql
    stage_type_data = [
        (6, "emf_id", "EMF ID", "EMF identification number", True),
        (7, "information_security", "במ", "Information security stage", False),
        (
            8,
            "letter_of_necessity",
            "מכתב נחיצות",
            "Letter of necessity of the purchase",
            False,
        ),
        (9, "bom", "BOM", "BOM of the purchase", False),
        (10, "bikushit_id", "מספר ביקושית", "Bikushit ID stage", True),
        (11, "demand_id", "מספר דרישה", "Demand ID Stage", True),
        (12, "mnhr", "מנהר", "Mnhr stage", False),
        (13, "Committees", "ועדות", "Committees stage", False),
        (14, "blm", "בלמ", "Blm stage", False),
        (15, "exemption_committee", "ועדת פטור", "Exemption committee stage", False),
        (16, "mission", "משלחת", "Mission stage", False),
        (
            17,
            "financing_deployment",
            "פריסת מימון",
            "Financing deployment stage",
            False,
        ),
        (18, "order_id", "מספר הזמנה", "Order ID stage", True),
    ]

    # Create stage types with explicit IDs
    for (
        stage_type_id,
        name,
        display_name,
        description,
        value_required,
    ) in stage_type_data:
        stage_type = StageType(
            id=stage_type_id,
            name=name,
            display_name=display_name,
            description=description,
            value_required=value_required,
        )
        session.add(stage_type)
        stage_type_ids.append(stage_type_id)

    session.flush()
    return stage_type_ids


def seed_predefined_flows(session: Any) -> list[int]:
    """Create predefined flows from backup data with correct parallel stage structure."""
    predefined_flow_ids = []

    # Define flows with their stage sequences from backup data (stage_type_id, priority)
    # Note: Multiple stages with same priority run in parallel
    flows_data = {
        "ILS_FLOW": [
            (6, 1),  # emf_id - priority 1
            (7, 2),  # information_security - priority 2
            (8, 2),  # letter_of_necessity - priority 2 (parallel with above)
            (9, 2),  # bom - priority 2 (parallel with above)
            (10, 3),  # bikushit_id - priority 3
            (
                7,
                4,
            ),  # information_security - priority 4 (duplicate stage type but different priority)
            (11, 5),  # demand_id - priority 5
            (12, 6),  # mnhr - priority 6
            (13, 7),  # Committees - priority 7
            (14, 8),  # blm - priority 8
            (18, 9),  # order_id - priority 9
        ],
        "SUPPORT_USD_FLOW": [
            (6, 1),  # emf_id - priority 1
            (7, 2),  # information_security - priority 2
            (8, 2),  # letter_of_necessity - priority 2 (parallel)
            (9, 2),  # bom - priority 2 (parallel)
            (10, 3),  # bikushit_id - priority 3
            (7, 4),  # information_security - priority 4
            (11, 5),  # demand_id - priority 5
            (16, 6),  # mission - priority 6
            (14, 7),  # blm - priority 7
            (18, 8),  # order_id - priority 8
        ],
        "AVAILABLE_USD_FLOW": [
            (6, 1),  # emf_id - priority 1
            (7, 2),  # information_security - priority 2
            (8, 2),  # letter_of_necessity - priority 2 (parallel)
            (9, 2),  # bom - priority 2 (parallel)
            (10, 3),  # bikushit_id - priority 3
            (7, 4),  # information_security - priority 4
            (11, 5),  # demand_id - priority 5
            (15, 6),  # exemption_committee - priority 6
            (16, 7),  # mission - priority 7
            (14, 8),  # blm - priority 8
            (18, 9),  # order_id - priority 9
        ],
        "MIXED_USD_FLOW": [
            (6, 1),  # emf_id - priority 1
            (7, 2),  # information_security - priority 2
            (8, 2),  # letter_of_necessity - priority 2 (parallel)
            (9, 2),  # bom - priority 2 (parallel)
            (10, 3),  # bikushit_id - priority 3
            (7, 4),  # information_security - priority 4
            (11, 5),  # demand_id - priority 5
            (15, 6),  # exemption_committee - priority 6
            (16, 7),  # mission - priority 7
            (14, 8),  # blm - priority 8
            (18, 9),  # order_id - priority 9
        ],
        "SUPPORT_USD_ABOVE_400K_FLOW": [
            (6, 1),  # emf_id - priority 1
            (7, 2),  # information_security - priority 2
            (8, 2),  # letter_of_necessity - priority 2 (parallel)
            (9, 2),  # bom - priority 2 (parallel)
            (10, 3),  # bikushit_id - priority 3
            (7, 4),  # information_security - priority 4
            (11, 5),  # demand_id - priority 5
            (12, 6),  # mnhr - priority 6
            (17, 7),  # financing_deployment - priority 7
            (16, 8),  # mission - priority 8
            (14, 9),  # blm - priority 9
            (18, 10),  # order_id - priority 10
        ],
        "MIXED_USD_ABOVE_400K_FLOW": [
            (6, 1),  # emf_id - priority 1
            (7, 2),  # information_security - priority 2
            (8, 2),  # letter_of_necessity - priority 2 (parallel)
            (9, 2),  # bom - priority 2 (parallel)
            (10, 3),  # bikushit_id - priority 3
            (7, 4),  # information_security - priority 4
            (11, 5),  # demand_id - priority 5
            (15, 6),  # exemption_committee - priority 6
            (12, 7),  # mnhr - priority 7
            (17, 8),  # financing_deployment - priority 8
            (16, 9),  # mission - priority 9
            (14, 10),  # blm - priority 10
            (18, 11),  # order_id - priority 11
        ],
    }

    # Create predefined flows with explicit IDs to match backup
    flow_ids = {
        "ILS_FLOW": 1,
        "SUPPORT_USD_FLOW": 2,
        "AVAILABLE_USD_FLOW": 3,
        "MIXED_USD_FLOW": 4,
        "SUPPORT_USD_ABOVE_400K_FLOW": 5,
        "MIXED_USD_ABOVE_400K_FLOW": 6,
    }

    for flow_name, stages in flows_data.items():
        # Create the predefined flow with explicit ID
        predefined_flow = PredefinedFlow(id=flow_ids[flow_name], flow_name=flow_name)
        session.add(predefined_flow)
        predefined_flow_ids.append(predefined_flow.id)

        # Create the predefined flow stages
        for stage_type_id, priority in stages:
            predefined_flow_stage = PredefinedFlowStage(
                predefined_flow_id=predefined_flow.id,
                stage_type_id=stage_type_id,
                priority=priority,
            )
            session.add(predefined_flow_stage)

    session.flush()
    return predefined_flow_ids


DESCRIPTIONS = [
    "Cloud infrastructure scaling for increased traffic demands",
    "PostgreSQL database migration to managed cloud service",
    "Implementation of S3-compatible storage solution",
    "Kubernetes cluster setup and container orchestration",
    "API gateway and microservices architecture deployment",
    "CI/CD pipeline automation and DevOps tooling",
    "Security monitoring and penetration testing services",
    "Redis cache implementation for performance optimization",
    "Load balancer configuration and auto-scaling setup",
    "Backup and disaster recovery system implementation",
]


def create_random_date(start_years_ago: int = 3, end_years_ago: int = 0) -> date:
    """Create a random date within the specified year range."""
    start_date = datetime.now() - timedelta(days=365 * start_years_ago)
    end_date = datetime.now() - timedelta(days=365 * end_years_ago)
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    random_date = start_date + timedelta(days=random_days)
    return random_date.date()


def create_random_datetime(
    start_years_ago: int = 3, end_years_ago: int = 0
) -> datetime:
    """Create a random datetime within the specified year range."""
    start_date = datetime.now() - timedelta(days=365 * start_years_ago)
    end_date = datetime.now() - timedelta(days=365 * end_years_ago)
    time_between = end_date - start_date
    seconds_between = int(time_between.total_seconds())
    random_seconds = random.randrange(seconds_between)
    random_datetime = start_date + timedelta(seconds=random_seconds)
    return random_datetime


def seed_suppliers(session: Any) -> list[int]:
    """Create supplier records and return their IDs."""
    supplier_ids = []
    for supplier_name in SUPPLIERS:
        supplier = Supplier(name=supplier_name)
        session.add(supplier)
        session.flush()
        supplier_ids.append(supplier.id)
    return supplier_ids


def seed_service_types_and_services(
    session: Any,
) -> tuple[list[int], dict[int, list[int]]]:
    """Create service types and services, return service_type_ids and services_by_type_id."""
    service_type_ids = []
    services_by_type_id = {}

    for service_type_name in SERVICE_TYPES:
        service_type = ServiceType(name=service_type_name)
        session.add(service_type)
        session.flush()
        service_type_ids.append(service_type.id)

        # Create services for this service type
        service_ids = []
        for service_name in SERVICES_BY_TYPE[service_type_name]:
            service = Service(name=service_name, service_type_id=service_type.id)
            session.add(service)
            session.flush()
            service_ids.append(service.id)

        services_by_type_id[service_type.id] = service_ids

    return service_type_ids, services_by_type_id


def create_random_stage_value() -> str:
    """Generate a random stage value."""
    return f"STAGE-{random.randint(100000, 999999)}"


def create_random_order_id() -> str:
    """Generate a random order ID."""
    return f"ORD-{random.randint(10000, 99999)}"


def create_random_demand_id() -> str:
    """Generate a random demand ID."""
    return f"DEM-{random.randint(10000, 99999)}"


def create_random_bikushit_id() -> str:
    """Generate a random bikushit ID."""
    return f"BIK-{random.randint(10000, 99999)}"


def create_random_stage_value_9_digits() -> str:
    """Generate a random 9-digit value for stages that require values."""
    return f"{random.randint(100000000, 999999999)}"


def complete_stages_for_purchase(session: Any, purchase_id: int) -> None:
    """Complete random stages for a purchase following priority order."""
    from sqlalchemy import select

    # Get all stages for this purchase ordered by priority
    stmt = (
        select(Stage).where(Stage.purchase_id == purchase_id).order_by(Stage.priority)
    )
    stages = session.execute(stmt).scalars().all()

    if not stages:
        return

    # Randomly decide how many stages to complete (0 to all stages)
    # More likely to complete earlier stages
    population_size = len(stages) + 1
    base_weights = [20, 15, 12, 10, 8, 6, 4, 3, 2, 1]
    # Extend weights if we have more stages than base weights
    if population_size > len(base_weights):
        base_weights.extend([1] * (population_size - len(base_weights)))

    num_stages_to_complete = random.choices(
        range(population_size),
        weights=base_weights[:population_size],
        k=1,
    )[0]

    if num_stages_to_complete == 0:
        return

    # Group stages by priority to handle parallel stages
    stages_by_priority = {}
    for stage in stages:
        if stage.priority not in stages_by_priority:
            stages_by_priority[stage.priority] = []
        stages_by_priority[stage.priority].append(stage)

    # Get sorted priority levels
    priority_levels = sorted(stages_by_priority.keys())

    # Complete stages following priority order
    completed_count = 0
    base_completion_date = create_random_datetime(
        2, 0.5
    )  # Start 2 years ago to 6 months ago

    for priority_level in priority_levels:
        if completed_count >= num_stages_to_complete:
            break

        priority_stages = stages_by_priority[priority_level]

        # For stages with the same priority, randomly decide how many to complete
        stages_to_complete_at_level = min(
            len(priority_stages), num_stages_to_complete - completed_count
        )

        # If we're completing some stages at this priority level,
        # randomly select which ones
        if stages_to_complete_at_level > 0:
            stages_to_complete = random.sample(
                priority_stages, stages_to_complete_at_level
            )

            for stage in stages_to_complete:
                # Load stage_type to check if value is required
                stage_type = session.get(StageType, stage.stage_type_id)

                # Set value if required
                if stage_type and stage_type.value_required:
                    stage.value = create_random_stage_value_9_digits()

                # Set completion date (add some time progression)
                stage.completion_date = base_completion_date + timedelta(
                    days=completed_count
                    * random.randint(1, 7),  # 1-7 days between completions
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                )

                completed_count += 1

        # Add extra time between priority levels
        base_completion_date += timedelta(days=random.randint(3, 14))


def get_predefined_flow_for_purchase_costs(costs: list[Cost]) -> str | None:
    """Return predefined flow name based on purchase costs (replicated from purchase service)."""
    if not costs:
        return None

    is_amount_above_400k = sum(cost.amount for cost in costs) >= 400_000

    if len(costs) > 1:
        if is_amount_above_400k:
            return "MIXED_USD_ABOVE_400K_FLOW"
        else:
            return "MIXED_USD_FLOW"

    cost = costs[0]

    if cost.currency == CurrencyEnum.SUPPORT_USD:
        if is_amount_above_400k:
            return "SUPPORT_USD_ABOVE_400K_FLOW"
        return "SUPPORT_USD_FLOW"

    elif cost.currency == CurrencyEnum.AVAILABLE_USD:
        return "AVAILABLE_USD_FLOW"

    return "ILS_FLOW"


def create_purchase_with_stages(session: Any, purpose_id: int) -> None:
    """Create a purchase with costs and auto-generated stages."""
    # Create purchase
    purchase = Purchase(purpose_id=purpose_id)
    session.add(purchase)
    session.flush()  # Get the purchase ID

    # Create 1-3 costs with random amounts and currencies
    num_costs = random.randint(1, 3)
    costs = []

    for _ in range(num_costs):
        currency = random.choice(list(CurrencyEnum))
        # Generate realistic amounts based on currency
        if currency == CurrencyEnum.ILS:
            amount = random.uniform(1000, 500000)  # 1K to 500K ILS
        else:  # USD currencies
            amount = random.uniform(100, 150000)  # $100 to $150K USD

        cost = Cost(
            purchase_id=purchase.id,
            currency=currency,
            amount=round(amount, 2),
        )
        session.add(cost)
        costs.append(cost)

    # Get predefined flow based on costs
    flow_name = get_predefined_flow_for_purchase_costs(costs)
    if flow_name:
        # Find the predefined flow by name
        from sqlalchemy import select

        stmt = select(PredefinedFlow).where(PredefinedFlow.flow_name == flow_name)
        predefined_flow = session.execute(stmt).scalar_one_or_none()

        if predefined_flow:
            purchase.predefined_flow_id = predefined_flow.id

            # Create stages based on predefined flow
            for predefined_stage in predefined_flow.predefined_flow_stages:
                stage = Stage(
                    stage_type_id=predefined_stage.stage_type_id,
                    priority=predefined_stage.priority,
                    purchase_id=purchase.id,
                )
                session.add(stage)

    session.flush()


def seed_purposes_with_purchases_and_costs(
    session: Any,
    supplier_ids: list[int],
    hierarchy_ids: list[int],
    service_type_ids: list[int],
    services_by_type_id: dict[int, list[int]],
    num_purposes: int = 100,
) -> None:
    """Create purposes with purchases and costs."""

    for _ in range(num_purposes):
        # Random purpose data
        creation_time = create_random_datetime(3, 0)
        expected_delivery = create_random_date(2, -1)  # Can be future dates

        purpose = Purpose(
            description=random.choice(DESCRIPTIONS),
            creation_time=creation_time,
            status=random.choice(list(StatusEnum)),
            comments=f"Generated test data on {datetime.now().strftime('%Y-%m-%d')}",
            last_modified=creation_time,
            expected_delivery=expected_delivery,
            hierarchy_id=random.choice(hierarchy_ids),
            supplier_id=random.choice(supplier_ids),
            service_type_id=random.choice(service_type_ids),
        )
        session.add(purpose)
        session.flush()

        # Add purpose contents (services)
        selected_service_type_id = purpose.service_type_id
        available_services = services_by_type_id[selected_service_type_id]

        # Add 1-3 services to each purpose
        num_services = random.randint(1, min(3, len(available_services)))
        selected_services = random.sample(available_services, num_services)

        for service_id in selected_services:
            content = PurposeContent(
                purpose_id=purpose.id,
                service_id=service_id,
                quantity=random.randint(1, 10),
            )
            session.add(content)

        # Create 1-2 purchases per purpose with costs and stages
        num_purchases = random.randint(1, 2)
        for _ in range(num_purchases):
            create_purchase_with_stages(session, purpose.id)


def get_session():
    """Create and return a database session."""
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
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def fix_sequence_sync(session: Any) -> None:
    """Fix sequence synchronization after inserting records with explicit IDs."""
    try:
        print("🔧 Synchronizing database sequences...")

        # Fix hierarchy sequence
        session.execute(
            "SELECT setval('hierarchy_id_seq', (SELECT MAX(id) FROM hierarchy))"
        )

        # Fix stage_type sequence
        session.execute(
            "SELECT setval('stage_type_id_seq', (SELECT MAX(id) FROM stage_type))"
        )

        # Fix predefined_flow sequence
        session.execute(
            "SELECT setval('predefined_flow_id_seq', (SELECT MAX(id) FROM predefined_flow))"
        )

        print("   ✅ Database sequences synchronized")

    except Exception as e:
        print(f"   ⚠️  Warning: Could not sync sequences: {e}")
        # Don't raise - this is not critical for SQLite or if sequences don't exist


def seed_base_data():
    """Create only stage types and predefined flows (base data)."""
    session = get_session()

    try:
        print("🌱 Starting base data seeding...")

        print("📋 Creating stage types from backup...")
        stage_type_ids = seed_stage_types(session)
        print(f"   Created {len(stage_type_ids)} stage types")

        print("🔄 Creating predefined flows...")
        predefined_flow_ids = seed_predefined_flows(session)
        print(f"   Created {len(predefined_flow_ids)} predefined flows")

        # Fix sequence synchronization after inserting with explicit IDs
        fix_sequence_sync(session)

        session.commit()
        print("✅ Base data seeding completed successfully!")

        print("\n📊 Base Data Summary:")
        print(f"   • Stage Types: {len(stage_type_ids)}")
        print(f"   • Predefined Flows: {len(predefined_flow_ids)}")

    except Exception as e:
        session.rollback()
        print(f"❌ Error during base data seeding: {e}")
        raise
    finally:
        session.close()


def seed_stage_data():
    """Complete random stages with values and completion dates."""
    session = get_session()

    try:
        print("🌱 Starting stage data seeding...")

        # Get all purchases to complete their stages
        from sqlalchemy import select

        stmt = select(Purchase)
        purchases = session.execute(stmt).scalars().all()

        if not purchases:
            print("   No purchases found. Run mock data seeding first.")
            return

        print(f"🎭 Completing stages for {len(purchases)} purchases...")

        for purchase in purchases:
            complete_stages_for_purchase(session, purchase.id)

        session.commit()
        print("✅ Stage data seeding completed successfully!")

        # Print summary
        total_stages = session.query(Stage).count()
        completed_stages = (
            session.query(Stage).filter(Stage.completion_date.isnot(None)).count()
        )
        stages_with_values = (
            session.query(Stage).filter(Stage.value.isnot(None)).count()
        )

        print("\n📊 Stage Data Summary:")
        print(f"   • Total Stages: {total_stages}")
        print(f"   • Completed Stages: {completed_stages}")
        print(f"   • Stages with Values: {stages_with_values}")
        print(
            f"   • Completion Rate: {completed_stages/total_stages*100:.1f}%"
            if total_stages > 0
            else "   • Completion Rate: 0%"
        )

    except Exception as e:
        session.rollback()
        print(f"❌ Error during stage data seeding: {e}")
        raise
    finally:
        session.close()


def seed_mock_data(num_purposes: int = 100):
    """Create all mock data including suppliers, hierarchies, service types, and purposes."""
    session = get_session()

    try:
        print("🌱 Starting mock data seeding...")

        # Check if data already exists
        existing_purposes = session.query(Purpose).count()
        if existing_purposes > 0:
            print(
                f"⚠️  Found {existing_purposes} existing purposes. Proceeding with seeding..."
            )

        print("📦 Creating suppliers...")
        supplier_ids = seed_suppliers(session)

        print("🏢 Creating hierarchies from backup...")
        existing_hierarchy_ids = get_existing_hierarchies(session)
        if existing_hierarchy_ids:
            print(
                f"   Found {len(existing_hierarchy_ids)} existing hierarchies, using them..."
            )
            hierarchy_ids = existing_hierarchy_ids
        else:
            print("   No existing hierarchies found, creating from backup data...")
            hierarchy_ids = seed_hierarchies_from_backup(session)
            print(f"   Created {len(hierarchy_ids)} hierarchies from backup")
            # Fix hierarchy sequence after inserting with explicit IDs
            fix_sequence_sync(session)

        print("🔧 Creating service types and services...")
        service_type_ids, services_by_type_id = seed_service_types_and_services(session)

        print(f"🎯 Creating {num_purposes} purposes with purchases and costs...")
        seed_purposes_with_purchases_and_costs(
            session,
            supplier_ids,
            hierarchy_ids,
            service_type_ids,
            services_by_type_id,
            num_purposes=num_purposes,
        )

        session.commit()
        print("✅ Mock data seeding completed successfully!")

        # Print summary
        total_purposes = session.query(Purpose).count()
        total_purchases = session.query(Purchase).count()
        total_costs = session.query(Cost).count()
        total_stages = session.query(Stage).count()
        total_service_types = session.query(ServiceType).count()
        total_services = session.query(Service).count()

        print("\n📊 Mock Data Summary:")
        print(f"   • Purposes: {total_purposes}")
        print(f"   • Purchases: {total_purchases}")
        print(f"   • Costs: {total_costs}")
        print(f"   • Stages: {total_stages}")
        print(f"   • Service Types: {total_service_types}")
        print(f"   • Services: {total_services}")
        print(f"   • Suppliers: {len(supplier_ids)}")
        print(f"   • Hierarchies: {len(hierarchy_ids)}")

    except Exception as e:
        session.rollback()
        print(f"❌ Error during mock data seeding: {e}")
        raise
    finally:
        session.close()


def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Database seeding script for Calculaud backend"
    )
    parser.add_argument(
        "--base-data-only",
        action="store_true",
        help="Create only stage types and predefined flows (base data)",
    )
    parser.add_argument(
        "--mock-data-only",
        action="store_true",
        help="Create only mock data (suppliers, hierarchies, purposes, etc.)",
    )
    parser.add_argument(
        "--stage-data-only",
        action="store_true",
        help="Complete random stages with values and completion dates",
    )
    parser.add_argument(
        "--num-purposes",
        type=int,
        default=100,
        help="Number of purposes to create for mock data (default: 100)",
    )

    args = parser.parse_args()

    if args.base_data_only:
        seed_base_data()
    elif args.mock_data_only:
        seed_mock_data(args.num_purposes)
    elif args.stage_data_only:
        seed_stage_data()
    else:
        # Default behavior: create all data
        print("🌱 Starting full database seeding...")
        seed_base_data()
        seed_mock_data(args.num_purposes)
        seed_stage_data()
        print("✅ Full database seeding completed successfully!")


if __name__ == "__main__":
    main()
