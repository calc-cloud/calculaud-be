"""Consolidated random data generation utilities."""

import random
from datetime import date, datetime, timedelta
from typing import Any

from app.costs.models import CurrencyEnum
from app.purposes.models import StatusEnum
from scripts.seeder.config.settings import SeedingConfig


def setup_random_seed(seed: int | None = None) -> None:
    """
    Set up random seed for reproducible results.

    Args:
        seed: Random seed to use. If None, uses SeedingConfig.RANDOM_SEED
    """
    if seed is None:
        seed = SeedingConfig.RANDOM_SEED
    random.seed(seed)


def create_random_date(start_years_ago: int = 3, end_years_ago: int = 0) -> date:
    """
    Create a random date within the specified year range.

    Args:
        start_years_ago: How many years ago to start the range
        end_years_ago: How many years ago to end the range (can be negative for future)

    Returns:
        Random date within the range
    """
    start_date = datetime.now() - timedelta(days=365 * start_years_ago)
    end_date = datetime.now() - timedelta(days=365 * end_years_ago)
    time_between = end_date - start_date
    days_between = time_between.days

    if days_between <= 0:
        return datetime.now().date()

    random_days = random.randrange(abs(days_between))
    random_date = start_date + timedelta(days=random_days)
    return random_date.date()


def create_random_datetime(
    start_years_ago: int = 3, end_years_ago: int = 0
) -> datetime:
    """
    Create a random datetime within the specified year range.

    Args:
        start_years_ago: How many years ago to start the range
        end_years_ago: How many years ago to end the range (can be negative for future)

    Returns:
        Random datetime within the range
    """
    start_date = datetime.now() - timedelta(days=365 * start_years_ago)
    end_date = datetime.now() - timedelta(days=365 * end_years_ago)
    time_between = end_date - start_date
    seconds_between = int(time_between.total_seconds())

    if seconds_between <= 0:
        return datetime.now()

    random_seconds = random.randrange(abs(seconds_between))
    random_datetime = start_date + timedelta(seconds=random_seconds)
    return random_datetime


def create_random_stage_value() -> str:
    """Generate a random stage value."""
    return f"STAGE-{random.randint(100000, 999999)}"


def create_random_stage_value_9_digits() -> str:
    """Generate a random 9-digit value for stages that require values."""
    return f"{random.randint(100000000, 999999999)}"


def create_random_order_id() -> str:
    """Generate a random order ID."""
    return f"ORD-{random.randint(10000, 99999)}"


def create_random_demand_id() -> str:
    """Generate a random demand ID."""
    return f"DEM-{random.randint(10000, 99999)}"


def create_random_bikushit_id() -> str:
    """Generate a random bikushit ID."""
    return f"BIK-{random.randint(10000, 99999)}"


def generate_random_cost_amount(currency: CurrencyEnum) -> int:
    """
    Generate realistic random amounts as integers in the 50K-1M range.

    Args:
        currency: Currency enum value

    Returns:
        Random integer amount between 50,000 and 1,000,000
    """
    return random.randint(50000, 1000000)


def get_random_status(include_new_statuses: bool = True) -> StatusEnum:
    """
    Get a random status value.

    Args:
        include_new_statuses: Whether to include new status values (SIGNED, PARTIALLY_SUPPLIED)

    Returns:
        Random StatusEnum value
    """
    if include_new_statuses:
        return random.choice(list(StatusEnum))
    else:
        # Only original statuses
        return random.choice([StatusEnum.IN_PROGRESS, StatusEnum.COMPLETED])


def get_random_currency() -> CurrencyEnum:
    """Get a random currency enum value."""
    return random.choice(list(CurrencyEnum))


def get_random_boolean(true_probability: float = 0.5) -> bool:
    """
    Get a random boolean with specified probability of True.

    Args:
        true_probability: Probability of returning True (0.0 to 1.0)

    Returns:
        Random boolean value
    """
    return random.random() < true_probability


def get_random_description() -> str:
    """Get a random purpose description."""
    return random.choice(SeedingConfig.get_purpose_descriptions())


def get_weighted_choice(items: list[Any], weights: list[int]) -> Any:
    """
    Make a weighted random choice from a list of items.

    Args:
        items: List of items to choose from
        weights: List of weights corresponding to items

    Returns:
        Randomly selected item based on weights
    """
    return random.choices(items, weights=weights, k=1)[0]


class MockDataGenerator:
    """Class for generating consistent mock data with relationships."""

    def __init__(self, seed: int | None = None):
        """
        Initialize the generator with optional seed.

        Args:
            seed: Random seed for reproducible results
        """
        setup_random_seed(seed)

    def generate_purpose_data(
        self,
        hierarchy_ids: list[int],
        supplier_ids: list[int],
        service_type_ids: list[int],
    ) -> dict[str, Any]:
        """
        Generate random data for a Purpose.

        Args:
            hierarchy_ids: Available hierarchy IDs
            supplier_ids: Available supplier IDs
            service_type_ids: Available service type IDs

        Returns:
            Dictionary with purpose data
        """
        creation_time = create_random_datetime(
            SeedingConfig.PURPOSE_CREATION_YEARS_AGO, 0
        )

        return {
            "description": get_random_description(),
            "creation_time": creation_time,
            "last_modified": creation_time,
            "status": get_random_status(),
            "comments": f"Generated test data on {datetime.now().strftime('%Y-%m-%d')}",
            "expected_delivery": create_random_date(
                2, -SeedingConfig.PURPOSE_DELIVERY_YEARS_FUTURE
            ),
            "hierarchy_id": random.choice(hierarchy_ids) if hierarchy_ids else None,
            "supplier_id": random.choice(supplier_ids) if supplier_ids else None,
            "service_type_id": (
                random.choice(service_type_ids) if service_type_ids else None
            ),
            "is_flagged": get_random_boolean(0.1),  # 10% chance of being flagged
        }

    def generate_cost_data(
        self, purchase_id: int, num_costs: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Generate random cost data for a purchase.

        Args:
            purchase_id: Purchase ID to associate costs with
            num_costs: Number of costs to generate (random 1-3 if None)

        Returns:
            List of cost data dictionaries
        """
        if num_costs is None:
            num_costs = random.randint(1, 3)

        costs = []
        for _ in range(num_costs):
            currency = get_random_currency()
            amount = generate_random_cost_amount(currency)

            costs.append(
                {
                    "purchase_id": purchase_id,
                    "currency": currency,
                    "amount": amount,
                }
            )

        return costs
