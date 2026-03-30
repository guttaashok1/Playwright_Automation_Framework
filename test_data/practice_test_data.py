"""
Test data constants and factory functions for practicesoftwaretesting.com (Tool Shop v5).

Known test accounts (seeded by the site):
  customer: customer@practicesoftwaretesting.com / welcome01
  admin:    admin@practicesoftwaretesting.com   / AQw3j6wBY

Known product IDs (stable in the seeded dataset):
  01JBMXQZK3VPVQ5PE71BKD5VMM  → Combination Pliers
  01JBMXQZK3VPVQ5PE71BKD5VML  → Pliers
  01JBMXQZK3VPVQ5PE71BKD5VMN  → Long Nose Pliers
"""
from __future__ import annotations

from faker import Faker

_fake = Faker()

# ── Static Credentials ────────────────────────────────────────────────────────

CUSTOMER_EMAIL    = "customer@practicesoftwaretesting.com"
CUSTOMER_PASSWORD = "welcome01"

ADMIN_EMAIL    = "admin@practicesoftwaretesting.com"
ADMIN_PASSWORD = "AQw3j6wBY"

# ── Site URLs ─────────────────────────────────────────────────────────────────

BASE_URL       = "https://practicesoftwaretesting.com"
API_BASE_URL   = "https://api.practicesoftwaretesting.com"

# ── Known Products ────────────────────────────────────────────────────────────

# Stable product names that exist in the seeded catalogue
PRODUCT_NAME_PLIERS    = "Combination Pliers"
PRODUCT_NAME_HAMMER    = "Hammer"
PRODUCT_NAME_SCREWDRIVER = "Screwdriver"
PRODUCT_SEARCH_QUERY   = "plier"       # partial match → multiple results

# Known category names
CATEGORY_HAND_TOOLS  = "Hand Tools"
CATEGORY_POWER_TOOLS = "Power Tools"
CATEGORY_HAMMERS     = "Hammers"

# ── Sort Options ──────────────────────────────────────────────────────────────

SORT_NAME_ASC   = "name,asc"
SORT_NAME_DESC  = "name,desc"
SORT_PRICE_ASC  = "price,asc"
SORT_PRICE_DESC = "price,desc"

# ── Dynamic User Factory ──────────────────────────────────────────────────────

def make_user(country: str = "US") -> dict:
    """Generate a unique set of registration data for a new user."""
    uid = _fake.unique.random_int(min=10_000, max=99_999)
    return {
        "first_name": _fake.first_name(),
        "last_name":  _fake.last_name(),
        "email":      f"testuser_{uid}@mailinator.com",
        "password":   f"Pw!{uid}#Aq9",
        "dob":        "1992-06-15",
        "street":     _fake.street_address(),
        "postcode":   _fake.zipcode(),
        "city":       _fake.city(),
        "state":      _fake.state(),
        "country":    country,
        "phone":      _fake.numerify("##########"),
    }


def make_billing(user: dict | None = None) -> dict:
    """Build billing dict compatible with PracticeCheckoutPage.fill_billing()."""
    u = user or make_user()
    return {
        "first_name": u["first_name"],
        "last_name":  u["last_name"],
        "address":    u["street"],
        "city":       u["city"],
        "state":      u["state"],
        "postcode":   u["postcode"],
        "country":    u["country"],
        "phone":      u["phone"],
        "email":      u["email"],
    }


# ── API Payloads ──────────────────────────────────────────────────────────────

def login_payload(email: str = CUSTOMER_EMAIL, password: str = CUSTOMER_PASSWORD) -> dict:
    return {"email": email, "password": password}


def register_payload(user: dict | None = None) -> dict:
    u = user or make_user()
    return {
        "first_name": u["first_name"],
        "last_name":  u["last_name"],
        "email":      u["email"],
        "password":   u["password"],
        "dob":        u.get("dob", "1992-06-15"),
        "phone":      u.get("phone", "1234567890"),
        "address": {
            "street":  u.get("street", "123 Test St"),
            "city":    u.get("city", "New York"),
            "state":   u.get("state", "NY"),
            "postcode":u.get("postcode", "10001"),
            "country": u.get("country", "US"),
        },
    }
