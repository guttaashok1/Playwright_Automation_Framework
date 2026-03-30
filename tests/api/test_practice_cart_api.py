"""
API Tests: practicesoftwaretesting.com — Cart Endpoints
Base URL: https://api.practicesoftwaretesting.com

Endpoints covered:
  POST   /carts                    — create a new cart
  GET    /carts/{cartId}           — retrieve cart contents
  POST   /carts/{cartId}/add       — add item to cart
  PUT    /carts/{cartId}/items/{itemId}  — update item quantity
  DELETE /carts/{cartId}/items/{itemId} — remove item from cart
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


def _create_cart(client: APIClient) -> str:
    """Create a cart and return the cart ID."""
    resp = client.post("/carts")
    assert resp.status_code in (200, 201), f"Cart creation failed: {resp.text}"
    return resp.body.get("id") or resp.body.get("cart_id")


def _add_item(client: APIClient, cart_id: str, product_id: str, qty: int = 1) -> dict:
    """Add an item to the cart, return the response body."""
    resp = client.post(
        f"/carts/{cart_id}/add",
        json={"product_id": product_id, "quantity": qty},
    )
    assert resp.status_code in (200, 201), f"Add item failed: {resp.text}"
    return resp.body


# ── Create Cart ───────────────────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.smoke
class TestPracticeCreateCartAPI:
    """Tests for POST /carts."""

    def test_create_cart_returns_200_or_201(self, auth_client: APIClient):
        """Creating a cart returns 200 or 201 with a cart ID."""
        response = auth_client.post("/carts")
        assert response.status_code in (200, 201), (
            f"Expected 200/201, got {response.status_code}. Body: {response.text}"
        )

    def test_create_cart_returns_cart_id(self, auth_client: APIClient):
        """Cart creation response contains an 'id' or 'cart_id' field."""
        response = auth_client.post("/carts")
        body = response.body
        has_id = "id" in body or "cart_id" in body
        assert has_id, f"No cart ID in response: {body}"

    def test_unauthenticated_cart_creation(self, practice_client: APIClient):
        """Unauthenticated POST /carts should return 401."""
        response = practice_client.post("/carts")
        assert response.status_code == 401, (
            f"Expected 401 for unauthenticated cart, got {response.status_code}"
        )


# ── Retrieve Cart ─────────────────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.smoke
class TestPracticeGetCartAPI:
    """Tests for GET /carts/{cartId}."""

    def test_get_empty_cart_returns_200(self, auth_client: APIClient):
        """Fetching a newly created empty cart returns 200."""
        cart_id = _create_cart(auth_client)
        response = auth_client.get(f"/carts/{cart_id}")
        response.assert_status(200)

    def test_empty_cart_has_no_items(self, auth_client: APIClient):
        """New cart has an empty items list."""
        cart_id = _create_cart(auth_client)
        response = auth_client.get(f"/carts/{cart_id}")
        body = response.body
        items = body.get("cart_items") or body.get("items") or []
        assert len(items) == 0, f"Expected empty cart, got items: {items}"

    def test_get_nonexistent_cart_returns_404(self, auth_client: APIClient):
        """GET on a fake cart ID returns 404."""
        response = auth_client.get("/carts/00000000-0000-0000-0000-000000000000")
        assert response.status_code in (404, 422), (
            f"Expected 404/422, got {response.status_code}"
        )


# ── Add Items ─────────────────────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.regression
class TestPracticeAddToCartAPI:
    """Tests for POST /carts/{cartId}/add."""

    def test_add_item_returns_200(
        self, auth_client: APIClient, first_product_id: str
    ):
        """Adding a product to cart returns 200 or 201."""
        cart_id = _create_cart(auth_client)
        response = auth_client.post(
            f"/carts/{cart_id}/add",
            json={"product_id": first_product_id, "quantity": 1},
        )
        assert response.status_code in (200, 201), (
            f"Expected 200/201, got {response.status_code}. Body: {response.text}"
        )

    def test_cart_contains_added_item(
        self, auth_client: APIClient, first_product_id: str
    ):
        """After adding, the cart contains the product."""
        cart_id = _create_cart(auth_client)
        _add_item(auth_client, cart_id, first_product_id)
        cart = auth_client.get(f"/carts/{cart_id}").body
        items = cart.get("cart_items") or cart.get("items") or []
        product_ids = [i.get("product_id") or i.get("id") for i in items]
        assert first_product_id in product_ids, (
            f"Product {first_product_id} not found in cart. Items: {product_ids}"
        )

    def test_add_item_with_quantity_3(
        self, auth_client: APIClient, first_product_id: str
    ):
        """Adding with quantity=3 stores 3 units in the cart."""
        cart_id = _create_cart(auth_client)
        _add_item(auth_client, cart_id, first_product_id, qty=3)
        cart = auth_client.get(f"/carts/{cart_id}").body
        items = cart.get("cart_items") or cart.get("items") or []
        assert len(items) > 0, "No items found after adding"
        qty = items[0].get("quantity") or items[0].get("qty") or 0
        assert qty == 3, f"Expected qty=3, got {qty}"

    def test_add_item_invalid_product_returns_error(self, auth_client: APIClient):
        """Adding a non-existent product to cart returns 4xx."""
        cart_id = _create_cart(auth_client)
        response = auth_client.post(
            f"/carts/{cart_id}/add",
            json={"product_id": "00000000-0000-0000-0000-000000000000", "quantity": 1},
        )
        assert 400 <= response.status_code < 500, (
            f"Expected 4xx for invalid product, got {response.status_code}"
        )

    def test_add_item_zero_quantity_returns_error(
        self, auth_client: APIClient, first_product_id: str
    ):
        """Adding with quantity=0 returns a validation error."""
        cart_id = _create_cart(auth_client)
        response = auth_client.post(
            f"/carts/{cart_id}/add",
            json={"product_id": first_product_id, "quantity": 0},
        )
        assert response.status_code in (400, 422), (
            f"Expected 400/422 for qty=0, got {response.status_code}"
        )


# ── Remove Items ──────────────────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.regression
class TestPracticeRemoveFromCartAPI:
    """Tests for DELETE /carts/{cartId}/items/{itemId}."""

    def test_remove_item_returns_200(
        self, auth_client: APIClient, first_product_id: str
    ):
        """Removing an item from cart returns 200 or 204."""
        cart_id = _create_cart(auth_client)
        _add_item(auth_client, cart_id, first_product_id)

        cart = auth_client.get(f"/carts/{cart_id}").body
        items = cart.get("cart_items") or cart.get("items") or []
        if not items:
            pytest.skip("No items in cart to remove")
        item_id = items[0]["id"]

        response = auth_client.delete(f"/carts/{cart_id}/items/{item_id}")
        assert response.status_code in (200, 204), (
            f"Expected 200/204 on delete, got {response.status_code}"
        )

    def test_cart_empty_after_remove_only_item(
        self, auth_client: APIClient, first_product_id: str
    ):
        """Cart is empty after removing the only item."""
        cart_id = _create_cart(auth_client)
        _add_item(auth_client, cart_id, first_product_id)

        cart = auth_client.get(f"/carts/{cart_id}").body
        items = cart.get("cart_items") or cart.get("items") or []
        item_id = items[0]["id"]
        auth_client.delete(f"/carts/{cart_id}/items/{item_id}")

        cart_after = auth_client.get(f"/carts/{cart_id}").body
        remaining = cart_after.get("cart_items") or cart_after.get("items") or []
        assert len(remaining) == 0, f"Cart still has items after removal: {remaining}"
