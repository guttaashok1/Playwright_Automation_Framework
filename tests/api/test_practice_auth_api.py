"""
API Tests: practicesoftwaretesting.com — Authentication Endpoints
Base URL: https://api.practicesoftwaretesting.com

Endpoints covered:
  POST /users/login   — authenticate and receive JWT
  POST /users/register — create a new user account
  GET  /users/me      — fetch authenticated user profile
"""
import pytest

from utils.api_client import APIClient
from test_data.practice_test_data import (
    CUSTOMER_EMAIL,
    CUSTOMER_PASSWORD,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    API_BASE_URL,
    make_user,
    login_payload,
    register_payload,
)


# ── Module-level client pointing at the practicesoftwaretesting API ────────────

@pytest.fixture(scope="module")
def practice_client():
    client = APIClient(base_url=API_BASE_URL)
    yield client
    client.close()


@pytest.fixture(scope="module")
def auth_client():
    """Client pre-authenticated as the seeded customer."""
    client = APIClient(base_url=API_BASE_URL)
    response = client.post("/users/login", json=login_payload())
    token = response.get_json_value("access_token")
    client.set_auth_token(token)
    yield client
    client.close()


# ── Login Tests ───────────────────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.smoke
class TestPracticeLoginAPI:
    """Smoke tests for POST /users/login."""

    def test_valid_login_returns_200_with_token(self, practice_client: APIClient):
        """Valid customer credentials return 200 and an access_token."""
        response = practice_client.post(
            "/users/login", json=login_payload(CUSTOMER_EMAIL, CUSTOMER_PASSWORD)
        )
        response.assert_status(200)
        response.assert_json_key("access_token")

    def test_admin_login_returns_200_with_token(self, practice_client: APIClient):
        """Admin credentials also return 200 and an access_token."""
        response = practice_client.post(
            "/users/login", json=login_payload(ADMIN_EMAIL, ADMIN_PASSWORD)
        )
        response.assert_status(200)
        response.assert_json_key("access_token")

    def test_token_is_bearer_format(self, practice_client: APIClient):
        """Returned token is a non-empty string suitable for Bearer auth."""
        response = practice_client.post(
            "/users/login", json=login_payload()
        )
        token = response.get_json_value("access_token")
        assert isinstance(token, str) and len(token) > 20, (
            f"Token looks invalid: {token!r}"
        )

    def test_invalid_password_returns_401(self, practice_client: APIClient):
        """Wrong password returns 401 Unauthorized."""
        response = practice_client.post(
            "/users/login",
            json=login_payload(CUSTOMER_EMAIL, "wrong_password_xyz"),
        )
        response.assert_status(401)

    def test_nonexistent_email_returns_401(self, practice_client: APIClient):
        """Non-existent email returns 401."""
        response = practice_client.post(
            "/users/login",
            json={"email": "nobody@nowhere.invalid", "password": "pass123"},
        )
        response.assert_status(401)

    def test_missing_email_returns_422(self, practice_client: APIClient):
        """Omitting email returns 422 Unprocessable Entity."""
        response = practice_client.post(
            "/users/login", json={"password": CUSTOMER_PASSWORD}
        )
        assert response.status_code in (400, 422), (
            f"Expected 400/422, got {response.status_code}"
        )

    def test_missing_password_returns_422(self, practice_client: APIClient):
        """Omitting password returns 422 Unprocessable Entity."""
        response = practice_client.post(
            "/users/login", json={"email": CUSTOMER_EMAIL}
        )
        assert response.status_code in (400, 422), (
            f"Expected 400/422, got {response.status_code}"
        )

    def test_empty_body_returns_error(self, practice_client: APIClient):
        """Empty request body returns 4xx error."""
        response = practice_client.post("/users/login", json={})
        assert 400 <= response.status_code < 500


# ── Register Tests ────────────────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.regression
class TestPracticeRegisterAPI:
    """Tests for POST /users/register."""

    def test_register_new_user_returns_201(self, practice_client: APIClient):
        """Registering with valid unique data returns 201 Created."""
        payload = register_payload(make_user())
        response = practice_client.post("/users/register", json=payload)
        assert response.status_code in (200, 201), (
            f"Expected 200/201, got {response.status_code}. Body: {response.text}"
        )

    def test_register_duplicate_email_returns_422(self, practice_client: APIClient):
        """Re-registering with the same email returns a conflict error."""
        response = practice_client.post(
            "/users/register",
            json=register_payload({"email": CUSTOMER_EMAIL, "password": "anything123",
                                   "first_name": "Dup", "last_name": "User",
                                   "dob": "1990-01-01", "phone": "5551234567",
                                   "address": {"street": "1 St", "city": "NY",
                                               "state": "NY", "postcode": "10001",
                                               "country": "US"}}),
        )
        assert response.status_code in (409, 422), (
            f"Expected 409/422 for duplicate email, got {response.status_code}"
        )

    def test_register_missing_email_returns_422(self, practice_client: APIClient):
        """Omitting email in registration returns 422."""
        payload = register_payload(make_user())
        payload.pop("email", None)
        response = practice_client.post("/users/register", json=payload)
        assert response.status_code in (400, 422)

    def test_register_missing_password_returns_422(self, practice_client: APIClient):
        """Omitting password in registration returns 422."""
        payload = register_payload(make_user())
        payload.pop("password", None)
        response = practice_client.post("/users/register", json=payload)
        assert response.status_code in (400, 422)


# ── Profile Tests ─────────────────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.smoke
class TestPracticeProfileAPI:
    """Tests for GET /users/me (authenticated)."""

    def test_get_own_profile_returns_200(self, auth_client: APIClient):
        """Authenticated GET /users/me returns 200 with user data."""
        response = auth_client.get("/users/me")
        response.assert_status(200)
        response.assert_json_key("email")

    def test_profile_email_matches_login(self, auth_client: APIClient):
        """Profile email matches the email used to log in."""
        response = auth_client.get("/users/me")
        response.assert_json_key("email", CUSTOMER_EMAIL)

    def test_unauthenticated_profile_returns_401(self, practice_client: APIClient):
        """GET /users/me without a token returns 401."""
        response = practice_client.get("/users/me")
        response.assert_status(401)

    def test_profile_contains_expected_fields(self, auth_client: APIClient):
        """User profile contains first_name, last_name, and email fields."""
        response = auth_client.get("/users/me")
        body = response.body
        assert isinstance(body, dict)
        for field in ("email", "first_name", "last_name"):
            assert field in body, f"Field '{field}' missing from profile: {list(body.keys())}"
