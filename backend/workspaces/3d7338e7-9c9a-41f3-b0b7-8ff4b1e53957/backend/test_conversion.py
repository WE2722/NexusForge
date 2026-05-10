import pytest
from fastapi.testclient import TestClient
from main import app
from config import settings
from datetime import datetime

client = TestClient(app)

def test_convert_currency_success():
    """Test successful currency conversion."""
    test_data = {
        "amount": 100.0,
        "from_currency": "EUR",
        "to_currency": "USD"
    }

    response = client.post(f"{settings.API_V1_STR}/currency/convert", json=test_data)
    assert response.status_code == 200
    data = response.json()

    assert data["amount"] == 100.0
    assert data["from_currency"] == "EUR"
    assert data["to_currency"] == "USD"
    assert "converted_amount" in data
    assert "rate" in data
    assert "timestamp" in data

    # Verify conversion (100 EUR * 1.07 USD/EUR = 107 USD)
    assert data["converted_amount"] == 107.0
    assert data["rate"] == 1.07

def test_convert_currency_same_currency():
    """Test conversion when from and to currency are the same."""
    test_data = {
        "amount": 50.0,
        "from_currency": "USD",
        "to_currency": "USD"
    }

    response = client.post(f"{settings.API_V1_STR}/currency/convert", json=test_data)
    assert response.status_code == 200
    data = response.json()

    assert data["amount"] == 50.0
    assert data["from_currency"] == "USD"
    assert data["to_currency"] == "USD"
    assert data["converted_amount"] == 50.0
    assert data["rate"] == 1.0

def test_convert_currency_invalid_amount():
    """Test conversion with invalid amount."""
    test_data = {
        "amount": -100.0,
        "from_currency": "EUR",
        "to_currency": "USD"
    }

    response = client.post(f"{settings.API_V1_STR}/currency/convert", json=test_data)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

def test_convert_currency_invalid_currency():
    """Test conversion with invalid currency."""
    test_data = {
        "amount": 100.0,
        "from_currency": "EUR",
        "to_currency": "XYZ"  # Invalid currency
    }

    response = client.post(f"{settings.API_V1_STR}/currency/convert", json=test_data)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/v1/currency/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["environment"] == settings.ENVIRONMENT
    assert "timestamp" in data

def test_get_rates():
    """Test get exchange rates endpoint."""
    response = client.get("/api/v1/currency/rates")
    assert response.status_code == 200
    data = response.json()

    assert "base_currency" in data
    assert "rates" in data
    assert "EUR" in data["rates"]
    assert "USD" in data["rates"]
    assert "MAD" in data["rates"]