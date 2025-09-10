"""Analytics utility functions."""

from app.analytics.schemas import CurrencyAmounts, MultiCurrencyAmount
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


def calculate_multi_currency_totals(
    currency_amounts: CurrencyAmounts,
) -> MultiCurrencyAmount:
    """Calculate totals across multiple currencies with proper conversion.

    Args:
        currency_amounts: CurrencyAmounts schema with individual currency amounts

    Returns:
        MultiCurrencyAmount: Object with all currency totals calculated
    """

    ils = currency_amounts.ils
    support_usd = currency_amounts.support_usd
    available_usd = currency_amounts.available_usd

    # Calculate totals
    # Convert ILS amount to USD for total USD calculation
    ils_in_usd = convert_currency(ils, CurrencyEnum.ILS, CurrencyEnum.SUPPORT_USD)
    total_usd = support_usd + available_usd + ils_in_usd

    # Convert USD amounts to ILS for total ILS calculation
    support_usd_in_ils = convert_currency(
        support_usd, CurrencyEnum.SUPPORT_USD, CurrencyEnum.ILS
    )
    available_usd_in_ils = convert_currency(
        available_usd, CurrencyEnum.AVAILABLE_USD, CurrencyEnum.ILS
    )
    total_ils = ils + support_usd_in_ils + available_usd_in_ils

    return MultiCurrencyAmount(
        ils=ils,
        support_usd=support_usd,
        available_usd=available_usd,
        total_usd=total_usd,
        total_ils=total_ils,
    )
