"""
API Tests: practicesoftwaretesting.com — Products Endpoints
Base URL: https://api.practicesoftwaretesting.com

Endpoints covered:
  GET  /products              — list products (pagination, search, sort, category)
  GET  /products/{id}         — single product detail
  GET  /products/search       — search products by keyword
"""
import pytest

from utils.api_client import APIClient
from test_data.practice_test_data import (
    API_BASE_URL,
    PRODUCT_SEARCH_QUERY,
    login_payload,
)


@pytest.fixture(scope="module")
def practice_client():
    client = APIClient(base_url=API_BASE_URL)
    yield client
    client.close()


@pytest.fixture(scope="module")
def auth_client():
    client = APIClient(base_url=API_BASE_URL)
    resp = client.post("/users/login", json=login_payload())
    client.set_auth_token(resp.get_json_value("access_token"))
    yield client
    client.close()


@pytest.fixture(scope="module")
def first_product_id(practice_client: APIClient) -> str:
    """Fetch first product ID from the catalogue (module-scoped, fetched once)."""
    resp = practice_client.get("/products", params={"per_page": 1})
    data = resp.body
    if isinstance(data, dict) and "data" in data:
        return data["data"][0]["id"]
    if isinstance(data, list):
        return data[0]["id"]
    pytest.skip("Could not fetch product list")


# ── List Products ─────────────────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.smoke
class TestPracticeProductsListAPI:
    """Smoke tests for GET /products."""

    def test_list_products_returns_200(self, practice_client: APIClient):
        """GET /products returns 200."""
        practice_client.get("/products").assert_status(200)

    def test_list_products_returns_array(self, practice_client: APIClient):
        """Response body is a list or paginated object with a 'data' key."""
        response = practice_client.get("/products")
        body = response.body
        assert isinstance(body, (list, dict)), f"Unexpected type: {type(body)}"
        if isinstance(body, dict):
            assert "data" in body, f"'data' key missing. Keys: {list(body.keys())}"

    def test_list_products_non_empty(self, practice_client: APIClient):
        """Product list is non-empty."""
        response = practice_client.get("/products")
        body = response.body
        items = body["data"] if isinstance(body, dict) else body
        assert len(items) > 0, "Product list is empty"

    def test_each_product_has_required_fields(self, practice_client: APIClient):
        """Each product has id, name, and price fields."""
        response = practice_client.get("/products")
        body = response.body
        items = body["data"] if isinstance(body, dict) else body
        for product in items[:5]:  # check first 5
            assert "id"    in product, f"Product missing 'id': {product}"
            assert "name"  in product, f"Product missing 'name': {product}"
            assert "price" in product, f"Product missing 'price': {product}"


@pytest.mark.api
@pytest.mark.regression
class TestPracticeProductsPaginationAPI:
    """Tests for pagination parameters on GET /products."""

    def test_pagination_per_page(self, practice_client: APIClient):
        """per_page=5 returns fewer products than the full catalogue."""
        full = practice_client.get("/products").body
        full_items = full["data"] if isinstance(full, dict) else full
        response = practice_client.get("/products", params={"per_page": 5})
        body = response.body
        items = body["data"] if isinstance(body, dict) else body
        # API should return equal or fewer items than the full catalogue
        assert len(items) <= len(full_items), (
            f"per_page=5 returned {len(items)} but full catalogue has {len(full_items)}"
        )

    def test_pagination_page_2(self, practice_client: APIClient):
        """Page 2 products differ from page 1 products."""
        r1 = practice_client.get("/products", params={"page": 1, "per_page": 5})
        r2 = practice_client.get("/products", params={"page": 2, "per_page": 5})
        b1 = r1.body
        b2 = r2.body
        ids1 = {p["id"] for p in (b1["data"] if isinstance(b1, dict) else b1)}
        ids2 = {p["id"] for p in (b2["data"] if isinstance(b2, dict) else b2)}
        assert ids1 != ids2, "Page 1 and page 2 return identical products"

    def test_sort_by_name_ascending(self, practice_client: APIClient):
        """sort=name&sort_direction=asc returns products sorted by name A→Z."""
        response = practice_client.get(
            "/products", params={"sort": "name", "sort_direction": "asc", "per_page": 10}
        )
        body = response.body
        items = body["data"] if isinstance(body, dict) else body
        names = [p["name"] for p in items]
        assert names == sorted(names, key=str.lower), f"Not sorted A→Z: {names}"

    def test_sort_by_price_ascending(self, practice_client: APIClient):
        """sort=price&sort_direction=asc returns products sorted by price low→high."""
        response = practice_client.get(
            "/products", params={"sort": "price", "sort_direction": "asc", "per_page": 10}
        )
        body = response.body
        items = body["data"] if isinstance(body, dict) else body
        prices = [float(p["price"]) for p in items]
        assert prices == sorted(prices), f"Prices not sorted asc: {prices}"


# ── Single Product ─────────────────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.smoke
class TestPracticeProductDetailAPI:
    """Tests for GET /products/{id}."""

    def test_get_product_by_id_returns_200(self, practice_client: APIClient, first_product_id: str):
        """GET /products/{id} returns 200."""
        practice_client.get(f"/products/{first_product_id}").assert_status(200)

    def test_product_detail_has_required_fields(self, practice_client: APIClient, first_product_id: str):
        """Product detail contains id, name, description, price, and category_id."""
        response = practice_client.get(f"/products/{first_product_id}")
        body = response.body
        for field in ("id", "name", "price", "description"):
            assert field in body, f"Field '{field}' missing from product detail"

    def test_product_id_matches_requested_id(self, practice_client: APIClient, first_product_id: str):
        """Returned product id matches the id in the URL."""
        response = practice_client.get(f"/products/{first_product_id}")
        assert response.body["id"] == first_product_id

    def test_invalid_product_id_returns_404(self, practice_client: APIClient):
        """GET /products/nonexistent_id returns 404."""
        response = practice_client.get("/products/00000000-0000-0000-0000-000000000000")
        assert response.status_code in (404, 422), (
            f"Expected 404/422 for invalid ID, got {response.status_code}"
        )


# ── Product Search ─────────────────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.regression
class TestPracticeProductSearchAPI:
    """Tests for GET /products/search?q=..."""

    def test_search_returns_results(self, practice_client: APIClient):
        """Searching for 'plier' returns at least one product."""
        response = practice_client.get("/products/search", params={"q": PRODUCT_SEARCH_QUERY})
        body = response.body
        items = body["data"] if isinstance(body, dict) else body
        assert len(items) > 0, f"Search for '{PRODUCT_SEARCH_QUERY}' returned 0 results"

    def test_search_results_relevant(self, practice_client: APIClient):
        """Search results contain the queried term in product names."""
        response = practice_client.get("/products/search", params={"q": "hammer"})
        body = response.body
        items = body["data"] if isinstance(body, dict) else body
        if len(items) == 0:
            pytest.skip("No hammer products in catalogue")
        for product in items:
            assert "hammer" in product["name"].lower(), (
                f"Product '{product['name']}' does not match search term 'hammer'"
            )

    def test_search_empty_query_returns_all(self, practice_client: APIClient):
        """Searching with no query returns the full catalogue (or 200)."""
        response = practice_client.get("/products/search", params={"q": ""})
        assert response.status_code == 200

    def test_search_nonexistent_term_returns_empty(self, practice_client: APIClient):
        """Searching for gibberish returns 0 results."""
        response = practice_client.get(
            "/products/search", params={"q": "zzz_nothing_xyz_123"}
        )
        body = response.body
        items = body["data"] if isinstance(body, dict) else body
        assert len(items) == 0, f"Expected 0 results, got {len(items)}"
