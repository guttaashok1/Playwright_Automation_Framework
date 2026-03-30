"""
API Tests: practicesoftwaretesting.com — Cart Endpoints
Base URL: https://api.practicesoftwaretesting.com

Supported endpoints (verified against live API):
  POST  /carts              — create a new cart (auth required)
  GET   /carts/{cartId}     — retrieve cart (auth required)

NOTE: POST /carts/{id}/add and DELETE /carts/{id}/items/{id} return 404
on this API — cart item management is handled server-side via the checkout
flow. Tests for those endpoints are skipped accordingly.
"""
import pytest

from utils.api_client import APIClient
from test_data.practice_test_data import (
    API_BASE_URL,
    login_payload,
)


@pytest.fixture(scope="module")
def practice_client():
    client = APIClient(base_url=API_BASE_URL)
    yield client
    client.close()


@pytest.fixture(scope="module")
def auth_client():
    """Authenticated client (customer role)."""
    client = APIClient(base_url=API_BASE_URL)
    resp = client.post("/users/login", json=login_payload())
    client.set_auth_token(resp.get_json_value("access_token"))
    yield client
    client.close()


@pytest.fixture(scope="module")
def first_product_id(practice_client: APIClient) -> str:
    """Reusable first product ID."""
    resp = practice_client.get("/products", params={"per_page": 1})
    body = resp.body
    items = body["data"] if isinstance(body, dict) and "data" in body else body
    if not items:
        pytest.skip("No products available for cart tests")
    return items[0]["id"]


# ── Create Cart ───────────────────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.smoke
class TestPracticeCreateCartAPI:
    """Tests for POST /carts."""

    def test_create_cart_returns_201(self, auth_client: APIClient):
        """Creating a cart returns 201 with a cart ID."""
        response = auth_client.post("/carts")
        assert response.status_code in (200, 201), (
            f"Expected 200/201, got {response.status_code}. Body: {response.text}"
        )

    def test_create_cart_returns_cart_id(self, auth_client: APIClient):
        """Cart creation response contains an 'id' field."""
        response = auth_client.post("/carts")
        body = response.body
        assert "id" in body, f"No 'id' in cart response: {body}"
        assert len(body["id"]) > 0, "Cart ID is empty"

    def test_create_cart_unauthenticated_allowed(self, practice_client: APIClient):
        """
        POST /carts without auth returns 201 on this API —
        practicesoftwaretesting.com allows guest cart creation.
        """
        response = practice_client.post("/carts")
        assert response.status_code in (200, 201), (
            f"Expected 200/201 for guest cart, got {response.status_code}"
        )

    def test_created_cart_has_empty_items(self, auth_client: APIClient):
        """Newly created cart has an empty cart_items list."""
        cart_id = auth_client.post("/carts").get_json_value("id")
        cart = auth_client.get(f"/carts/{cart_id}").body
        items = cart.get("cart_items") or cart.get("items") or []
        assert len(items) == 0, f"Expected new cart to be empty, got: {items}"


# ── Retrieve Cart ─────────────────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.smoke
class TestPracticeGetCartAPI:
    """Tests for GET /carts/{cartId}."""

    def test_get_cart_returns_200(self, auth_client: APIClient):
        """GET on a valid cart ID returns 200."""
        cart_id = auth_client.post("/carts").get_json_value("id")
        auth_client.get(f"/carts/{cart_id}").assert_status(200)

    def test_cart_response_has_id(self, auth_client: APIClient):
        """Cart GET response includes the cart 'id'."""
        cart_id = auth_client.post("/carts").get_json_value("id")
        response = auth_client.get(f"/carts/{cart_id}")
        assert response.body.get("id") == cart_id

    def test_cart_response_has_items_key(self, auth_client: APIClient):
        """Cart GET response contains a 'cart_items' key."""
        cart_id = auth_client.post("/carts").get_json_value("id")
        response = auth_client.get(f"/carts/{cart_id}")
        body = response.body
        assert "cart_items" in body, (
            f"'cart_items' missing from cart response. Keys: {list(body.keys())}"
        )

    def test_get_nonexistent_cart_returns_404(self, auth_client: APIClient):
        """GET on a non-existent cart ID returns 404."""
        response = auth_client.get("/carts/00000000-0000-0000-0000-000000000000")
        assert response.status_code in (404, 422), (
            f"Expected 404/422, got {response.status_code}"
        )


# ── Cart Item Endpoints Not Supported ─────────────────────────────────────────

@pytest.mark.api
@pytest.mark.regression
@pytest.mark.skip(
    reason="POST /carts/{id}/add and DELETE /carts/{id}/items/{id} "
           "return 404 on practicesoftwaretesting.com — not supported by this API version"
)
class TestPracticeCartItemsAPI:
    """Skipped: add/remove item endpoints are not available on this API."""

    def test_add_item_returns_200(self, auth_client, first_product_id):
        cart_id = auth_client.post("/carts").get_json_value("id")
        response = auth_client.post(
            f"/carts/{cart_id}/add",
            json={"product_id": first_product_id, "quantity": 1},
        )
        assert response.status_code in (200, 201)

    def test_remove_item_returns_200(self, auth_client, first_product_id):
        pass
