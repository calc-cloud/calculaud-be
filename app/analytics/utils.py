"""Analytics utility functions."""

from app.config import settings
from app.costs.models import CurrencyEnum


def convert_currency(
    amount: float, from_currency: CurrencyEnum, to_currency: CurrencyEnum
) -> float:
    """Convert currency using the configured rate."""
    if from_currency == to_currency:
        return amount

    # Convert USD amounts
    if from_currency in [CurrencyEnum.SUPPORT_USD, CurrencyEnum.AVAILABLE_USD]:
        if to_currency == CurrencyEnum.ILS:
            return amount * settings.usd_to_ils_rate

    # Convert ILS amounts
    elif from_currency == CurrencyEnum.ILS:
        if to_currency in [CurrencyEnum.SUPPORT_USD, CurrencyEnum.AVAILABLE_USD]:
            return amount / settings.usd_to_ils_rate

    return amount
