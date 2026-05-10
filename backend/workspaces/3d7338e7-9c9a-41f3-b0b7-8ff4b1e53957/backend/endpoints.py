from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Annotated

from models.schemas import (
    CurrencyConversionRequest,
    CurrencyConversionResponse,
    HealthCheckResponse
)
from services.currency import CurrencyService
from dependencies import get_current_active_user
from config import settings

router = APIRouter(prefix=f"{settings.API_V1_STR}/currency", tags=["currency"])

@router.post(
    "/convert",
    response_model=CurrencyConversionResponse,
    summary="Convert currency amount",
    response_description="Returns the converted amount with rate details",
    status_code=status.HTTP_200_OK
)
async def convert_currency(
    request: CurrencyConversionRequest,
    current_user: Annotated[str, Depends(get_current_active_user)]
) -> CurrencyConversionResponse:
    """
    Convert an amount from one currency to another using fixed exchange rates.

    - **amount**: The amount to convert (must be positive)
    - **from_currency**: Source currency (EUR, USD, MAD)
    - **to_currency**: Target currency (EUR, USD, MAD)
    """
    try:
        conversion_result = CurrencyService.convert_amount(
            amount=request.amount,
            from_currency=request.from_currency,
            to_currency=request.to_currency
        )

        return CurrencyConversionResponse(
            amount=conversion_result["amount"],
            from_currency=conversion_result["from_currency"],
            to_currency=conversion_result["to_currency"],
            converted_amount=conversion_result["converted_amount"],
            rate=conversion_result["rate"],
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health check endpoint",
    response_description="Returns the health status of the service"
)
async def health_check() -> HealthCheckResponse:
    """Check the health status of the currency converter service."""
    return HealthCheckResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        timestamp=datetime.utcnow()
    )

@router.get(
    "/rates",
    summary="Get current exchange rates",
    response_description="Returns the fixed exchange rates"
)
async def get_exchange_rates() -> dict:
    """Get the current fixed exchange rates."""
    return {
        "base_currency": "EUR",
        "rates": settings.FIXED_RATES
    }