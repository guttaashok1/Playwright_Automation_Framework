"""
API Tests: Authentication Endpoints
Demonstrates direct REST API testing with APIClient.
"""
import pytest

from utils.api_client import APIClient
from configs.config import config


@pytest.mark.api
@pytest.mark.smoke
class TestAuthAPI:
    """Tests targeting the /auth endpoints."""

    def test_login_with_valid_credentials_returns_200(self, api_client: APIClient):
        """POST /auth/login with valid creds should return 200 and a token."""
        response = api_client.post(
            "/auth/login",
            json={"email": config.credentials.EMAIL, "password": config.credentials.PASSWORD},
        )
        response.assert_status(200)
        response.assert_json_key("token")

    def test_login_with_invalid_password_returns_401(self, api_client: APIClient):
        """POST /auth/login with wrong password should return 401."""
        response = api_client.post(
            "/auth/login",
            json={"email": config.credentials.EMAIL, "password": "wrong_password"},
        )
        response.assert_status(401)

    def test_login_missing_email_returns_400(self, api_client: APIClient):
        """POST /auth/login without email should return 400 validation error."""
        response = api_client.post("/auth/login", json={"password": "somepassword"})
        response.assert_status(400)

    def test_protected_endpoint_without_token_returns_401(self, api_client: APIClient):
        """Accessing a protected endpoint without auth should return 401."""
        response = api_client.get("/users/me")
        response.assert_status(401)

    def test_protected_endpoint_with_valid_token_returns_200(self, authenticated_api_client: APIClient):
        """Accessing a protected endpoint with valid JWT should return 200."""
        response = authenticated_api_client.get("/users/me")
        response.assert_status(200)
        response.assert_json_key("email")


@pytest.mark.api
@pytest.mark.regression
class TestUsersAPI:
    """Tests targeting the /users endpoints."""

    def test_get_current_user_profile(self, authenticated_api_client: APIClient):
        """GET /users/me should return the authenticated user's profile."""
        response = authenticated_api_client.get("/users/me")
        response.assert_ok()
        response.assert_json_key("email", config.credentials.EMAIL)

    def test_update_user_profile(self, authenticated_api_client: APIClient):
        """PATCH /users/me should update user fields."""
        response = authenticated_api_client.patch(
            "/users/me",
            json={"firstName": "Test", "lastName": "User"},
        )
        response.assert_ok()

    @pytest.mark.parametrize("missing_field", ["email", "password"])
    def test_create_user_missing_required_field_returns_400(
        self, api_client: APIClient, missing_field: str
    ):
        """POST /users with a missing required field should return 400."""
        payload = {
            "email": "newuser@example.com",
            "password": "Str0ngP@ss!",
            "firstName": "New",
            "lastName": "User",
        }
        del payload[missing_field]
        response = api_client.post("/users", json=payload)
        response.assert_status(400)
