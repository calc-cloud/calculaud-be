#!/usr/bin/env python3
"""
Database seeding script for creating random purposes with EMFs and costs.
Populates data over the last few years with various service types and services.
"""

import random
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.costs.models import Cost, CurrencyEnum
from app.database import Base
from app.emfs.models import EMF
from app.hierarchies.models import Hierarchy, HierarchyTypeEnum
from app.purposes.models import Purpose, PurposeContent, StatusEnum
from app.service_types.models import ServiceType
from app.services.models import Service
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


def seed_comprehensive_hierarchies(session: Any) -> list[int]:
    """Create a comprehensive hierarchy structure and return all hierarchy IDs."""
    hierarchy_ids = []
    
    # Organization structure data - realistic IT/Government organization
    org_structure = {
        # UNIT level (top level - organization units)
        "units": [
            "Ministry of Defense",
            "Ministry of Health", 
            "Ministry of Education",
        ],
        # CENTER level (major divisions within units)
        "centers": {
            "Ministry of Defense": ["Technology Division", "Operations Division", "Logistics Division"],
            "Ministry of Health": ["Digital Health Division", "Infrastructure Division"],
            "Ministry of Education": ["Educational Technology Division", "Administrative Systems Division"],
        },
        # ANAF level (branches within centers)
        "anafs": {
            "Technology Division": ["Cloud Services Branch", "Cybersecurity Branch", "Software Development Branch"],
            "Operations Division": ["Command Systems Branch", "Communications Branch"],
            "Logistics Division": ["Supply Chain Systems Branch", "Asset Management Branch"],
            "Digital Health Division": ["Patient Systems Branch", "Medical Records Branch"],
            "Infrastructure Division": ["Network Operations Branch", "Data Center Branch"],
            "Educational Technology Division": ["Learning Management Branch", "Student Information Branch"],
            "Administrative Systems Division": ["HR Systems Branch", "Financial Systems Branch"],
        },
        # MADOR level (departments within branches)
        "madorn": {
            "Cloud Services Branch": ["AWS Department", "Azure Department", "Infrastructure Department"],
            "Cybersecurity Branch": ["Security Operations Department", "Compliance Department"],
            "Software Development Branch": ["Backend Development Department", "Frontend Development Department"],
            "Command Systems Branch": ["Command Center Department", "Tactical Systems Department"],
            "Communications Branch": ["Radio Systems Department", "Network Communications Department"],
            "Supply Chain Systems Branch": ["Procurement Systems Department", "Inventory Management Department"],
            "Asset Management Branch": ["Equipment Tracking Department", "Maintenance Systems Department"],
            "Patient Systems Branch": ["Electronic Health Records Department", "Telemedicine Department"],
            "Medical Records Branch": ["Records Management Department", "Data Analytics Department"],
            "Network Operations Branch": ["Network Monitoring Department", "Infrastructure Support Department"],
            "Data Center Branch": ["Server Operations Department", "Storage Systems Department"],
            "Learning Management Branch": ["LMS Development Department", "Content Management Department"],
            "Student Information Branch": ["Student Records Department", "Academic Systems Department"],
            "HR Systems Branch": ["Payroll Systems Department", "Employee Management Department"],
            "Financial Systems Branch": ["Accounting Systems Department", "Budget Management Department"],
        },
        # TEAM level (operational teams within departments)
        "teams": {
            "AWS Department": ["EC2 Team", "S3 Team", "RDS Team"],
            "Azure Department": ["Virtual Machines Team", "Storage Team", "Database Team"],
            "Infrastructure Department": ["Network Team", "Security Team", "Monitoring Team"],
            "Security Operations Department": ["SOC Team", "Incident Response Team", "Threat Intelligence Team"],
            "Compliance Department": ["Audit Team", "Risk Assessment Team"],
            "Backend Development Department": ["API Team", "Database Team", "Microservices Team"],
            "Frontend Development Department": ["Web UI Team", "Mobile Team", "UX Team"],
            "Command Center Department": ["Operations Team", "Coordination Team"],
            "Tactical Systems Department": ["Systems Integration Team", "Field Support Team"],
            "Radio Systems Department": ["Communications Team", "Maintenance Team"],
            "Network Communications Department": ["Network Team", "Protocol Team"],
            "Procurement Systems Department": ["Development Team", "Integration Team"],
            "Inventory Management Department": ["Systems Team", "Analytics Team"],
            "Equipment Tracking Department": ["RFID Team", "Database Team"],
            "Maintenance Systems Department": ["Scheduling Team", "Mobile Team"],
            "Electronic Health Records Department": ["EHR Team", "Integration Team"],
            "Telemedicine Department": ["Platform Team", "Support Team"],
            "Records Management Department": ["Archival Team", "Retrieval Team"],
            "Data Analytics Department": ["Analytics Team", "Reporting Team"],
            "Network Monitoring Department": ["NOC Team", "Performance Team"],
            "Infrastructure Support Department": ["Hardware Team", "Software Team"],
            "Server Operations Department": ["Linux Team", "Windows Team"],
            "Storage Systems Department": ["SAN Team", "Backup Team"],
            "LMS Development Department": ["Development Team", "Testing Team"],
            "Content Management Department": ["Content Team", "Media Team"],
            "Student Records Department": ["Records Team", "Reporting Team"],
            "Academic Systems Department": ["Grading Team", "Scheduling Team"],
            "Payroll Systems Department": ["Processing Team", "Compliance Team"],
            "Employee Management Department": ["HRIS Team", "Benefits Team"],
            "Accounting Systems Department": ["GL Team", "AP/AR Team"],
            "Budget Management Department": ["Planning Team", "Tracking Team"],
        }
    }
    
    # Create UNIT level hierarchies
    unit_hierarchies = {}
    for unit_name in org_structure["units"]:
        unit = Hierarchy(
            type=HierarchyTypeEnum.UNIT,
            name=unit_name,
            path=unit_name,
            parent_id=None
        )
        session.add(unit)
        session.flush()
        unit_hierarchies[unit_name] = unit
        hierarchy_ids.append(unit.id)
    
    # Create CENTER level hierarchies
    center_hierarchies = {}
    for unit_name, centers in org_structure["centers"].items():
        parent_unit = unit_hierarchies[unit_name]
        for center_name in centers:
            center = Hierarchy(
                type=HierarchyTypeEnum.CENTER,
                name=center_name,
                path=f"{parent_unit.path} / {center_name}",
                parent_id=parent_unit.id
            )
            session.add(center)
            session.flush()
            center_hierarchies[center_name] = center
            hierarchy_ids.append(center.id)
    
    # Create ANAF level hierarchies
    anaf_hierarchies = {}
    for center_name, anafs in org_structure["anafs"].items():
        parent_center = center_hierarchies[center_name]
        for anaf_name in anafs:
            anaf = Hierarchy(
                type=HierarchyTypeEnum.ANAF,
                name=anaf_name,
                path=f"{parent_center.path} / {anaf_name}",
                parent_id=parent_center.id
            )
            session.add(anaf)
            session.flush()
            anaf_hierarchies[anaf_name] = anaf
            hierarchy_ids.append(anaf.id)
    
    # Create MADOR level hierarchies
    mador_hierarchies = {}
    for anaf_name, madorn in org_structure["madorn"].items():
        parent_anaf = anaf_hierarchies[anaf_name]
        for mador_name in madorn:
            mador = Hierarchy(
                type=HierarchyTypeEnum.MADOR,
                name=mador_name,
                path=f"{parent_anaf.path} / {mador_name}",
                parent_id=parent_anaf.id
            )
            session.add(mador)
            session.flush()
            mador_hierarchies[mador_name] = mador
            hierarchy_ids.append(mador.id)
    
    # Create TEAM level hierarchies
    for mador_name, teams in org_structure["teams"].items():
        parent_mador = mador_hierarchies[mador_name]
        for team_name in teams:
            team = Hierarchy(
                type=HierarchyTypeEnum.TEAM,
                name=team_name,
                path=f"{parent_mador.path} / {team_name}",
                parent_id=parent_mador.id
            )
            session.add(team)
            session.flush()
            hierarchy_ids.append(team.id)
    
    return hierarchy_ids


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


def create_random_emf_id() -> str:
    """Generate a random EMF ID."""
    return f"EMF-{random.randint(100000, 999999)}"


def create_random_order_id() -> str:
    """Generate a random order ID."""
    return f"ORD-{random.randint(10000, 99999)}"


def create_random_demand_id() -> str:
    """Generate a random demand ID."""
    return f"DEM-{random.randint(10000, 99999)}"


def create_random_bikushit_id() -> str:
    """Generate a random bikushit ID."""
    return f"BIK-{random.randint(10000, 99999)}"


def seed_purposes_with_emfs_and_costs(
    session: Any,
    supplier_ids: list[int],
    hierarchy_ids: list[int],
    service_type_ids: list[int],
    services_by_type_id: dict[int, list[int]],
    num_purposes: int = 100,
) -> None:
    """Create purposes with EMFs and costs."""

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

        # Create 1-3 EMFs for each purpose
        num_emfs = random.randint(1, 3)
        for _ in range(num_emfs):
            emf_creation_date = create_random_date(3, 0)

            emf = EMF(
                emf_id=create_random_emf_id(),
                purpose_id=purpose.id,
                creation_date=emf_creation_date,
                order_id=create_random_order_id() if random.random() > 0.3 else None,
                order_creation_date=(
                    create_random_date(2, 0) if random.random() > 0.3 else None
                ),
                demand_id=create_random_demand_id() if random.random() > 0.4 else None,
                demand_creation_date=(
                    create_random_date(2, 0) if random.random() > 0.4 else None
                ),
                bikushit_id=(
                    create_random_bikushit_id() if random.random() > 0.5 else None
                ),
                bikushit_creation_date=(
                    create_random_date(1, 0) if random.random() > 0.5 else None
                ),
            )
            session.add(emf)
            session.flush()

            # Create 1-2 costs for each EMF with currency restrictions
            num_costs = random.randint(1, 2)

            # Choose currency type - either all USD types or ILS only
            currency_options = list(CurrencyEnum)
            usd_currencies = [c for c in currency_options if "USD" in c.value]
            ils_currencies = [c for c in currency_options if c.value == "ILS"]

            # Pick either USD group or ILS
            if random.random() > 0.5:
                available_currencies = usd_currencies
            else:
                available_currencies = ils_currencies

            for _ in range(num_costs):
                cost = Cost(
                    emf_id=emf.id,
                    currency=random.choice(available_currencies),
                    amount=round(random.uniform(500.0, 100000.0), 2),
                )
                session.add(cost)


def main():
    """Main seeding function."""
    # Create engine and session using app configuration
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

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    try:
        print("🌱 Starting database seeding...")

        # Check if data already exists
        existing_purposes = session.query(Purpose).count()
        if existing_purposes > 0:
            print(
                f"⚠️  Found {existing_purposes} existing purposes. Proceeding with seeding..."
            )

        print("📦 Creating suppliers...")
        supplier_ids = seed_suppliers(session)

        print("🏢 Creating comprehensive hierarchy structure...")
        existing_hierarchy_ids = get_existing_hierarchies(session)
        if existing_hierarchy_ids:
            print(f"   Found {len(existing_hierarchy_ids)} existing hierarchies, using them...")
            hierarchy_ids = existing_hierarchy_ids
        else:
            print("   No existing hierarchies found, creating comprehensive structure...")
            hierarchy_ids = seed_comprehensive_hierarchies(session)
            print(f"   Created {len(hierarchy_ids)} hierarchies across 5 levels")

        print("🔧 Creating service types and services...")
        service_type_ids, services_by_type_id = seed_service_types_and_services(session)

        print("🎯 Creating purposes with EMFs and costs...")
        seed_purposes_with_emfs_and_costs(
            session,
            supplier_ids,
            hierarchy_ids,
            service_type_ids,
            services_by_type_id,
            num_purposes=100,
        )

        session.commit()
        print("✅ Database seeding completed successfully!")

        # Print summary
        total_purposes = session.query(Purpose).count()
        total_emfs = session.query(EMF).count()
        total_costs = session.query(Cost).count()
        total_service_types = session.query(ServiceType).count()
        total_services = session.query(Service).count()

        print("\n📊 Summary:")
        print(f"   • Purposes: {total_purposes}")
        print(f"   • EMFs: {total_emfs}")
        print(f"   • Costs: {total_costs}")
        print(f"   • Service Types: {total_service_types}")
        print(f"   • Services: {total_services}")
        print(f"   • Suppliers: {len(supplier_ids)}")
        print(f"   • Hierarchies: {len(hierarchy_ids)}")

    except Exception as e:
        session.rollback()
        print(f"❌ Error during seeding: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
