from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from .enums import Currency

class CurrencyConversionRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to convert (must be positive)")
    from_currency: Currency = Field(..., description="Source currency")
    to_currency: Currency = Field(..., description="Target currency")

    @validator("from_currency", "to_currency")
    def validate_currencies(cls, v):
        if v not in ["EUR", "USD", "MAD"]:
            raise ValueError("Currency must be one of: EUR, USD, MAD")
        return v

class CurrencyConversionResponse(BaseModel):
    amount: float
    from_currency: Currency
    to_currency: Currency
    converted_amount: float
    rate: float
    timestamp: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class HealthCheckResponse(BaseModel):
    status: str
    environment: str
    timestamp: datetime