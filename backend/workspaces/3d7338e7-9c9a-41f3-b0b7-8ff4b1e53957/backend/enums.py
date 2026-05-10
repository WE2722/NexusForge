from enum import Enum

class Currency(str, Enum):
    EUR = "EUR"
    USD = "USD"
    MAD = "MAD"

class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"