from typing import Dict
from fastapi import HTTPException, status
from config import settings
from models.enums import Currency

class CurrencyService:
    @staticmethod
    def get_conversion_rate(from_currency: Currency, to_currency: Currency) -> float:
        """Get the conversion rate between two currencies using fixed rates."""
        if from_currency == to_currency:
            return 1.0

        rates = settings.FIXED_RATES

        # Convert from_currency to EUR (base currency)
        if from_currency == Currency.EUR:
            from_rate = 1.0
        else:
            from_rate = 1.0 / rates[from_currency]

        # Convert EUR to to_currency
        if to_currency == Currency.EUR:
            to_rate = 1.0
        else:
            to_rate = rates[to_currency]

        # Calculate the direct rate
        return from_rate * to_rate

    @staticmethod
    def convert_amount(
        amount: float,
        from_currency: Currency,
        to_currency: Currency
    ) -> Dict:
        """Convert an amount from one currency to another."""
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be positive"
            )

        rate = CurrencyService.get_conversion_rate(from_currency, to_currency)
        converted_amount = amount * rate

        return {
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": round(converted_amount, 2),
            "rate": round(rate, 4),
        }