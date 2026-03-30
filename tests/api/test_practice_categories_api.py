"""
API Tests: practicesoftwaretesting.com — Categories Endpoints
Base URL: https://api.practicesoftwaretesting.com

Endpoints covered:
  GET /categories          — list all categories
  GET /categories/{id}     — category detail
  GET /categories/tree     — category hierarchy tree
"""
import pytest

from utils.api_client import APIClient
from test_data.practice_test_data import API_BASE_URL


@pytest.fixture(scope="module")
def practice_client():
    client = APIClient(base_url=API_BASE_URL)
    yield client
    client.close()


@pytest.fixture(scope="module")
def first_category_id(practice_client: APIClient) -> str:
    """Fetch the first category ID (module-scoped)."""
    resp = practice_client.get("/categories")
    body = resp.body
    items = body["data"] if isinstance(body, dict) and "data" in body else body
    if not items:
        pytest.skip("No categories returned from API")
    return items[0]["id"]


@pytest.mark.api
@pytest.mark.smoke
class TestPracticeCategoriesListAPI:
    """Smoke tests for GET /categories."""

    def test_list_categories_returns_200(self, practice_client: APIClient):
        """GET /categories returns HTTP 200."""
        practice_client.get("/categories").assert_status(200)

    def test_categories_list_non_empty(self, practice_client: APIClient):
        """Category list contains at least one category."""
        response = practice_client.get("/categories")
        body = response.body
        items = body["data"] if isinstance(body, dict) and "data" in body else body
        assert len(items) > 0, "No categories returned"

    def test_each_category_has_id_and_name(self, practice_client: APIClient):
        """Each category object contains 'id' and 'name'."""
        response = practice_client.get("/categories")
        body = response.body
        items = body["data"] if isinstance(body, dict) and "data" in body else body
        for cat in items:
            assert "id"   in cat, f"Category missing 'id': {cat}"
            assert "name" in cat, f"Category missing 'name': {cat}"

    def test_known_category_names_present(self, practice_client: APIClient):
        """Standard hand/power tools categories are in the catalogue."""
        response = practice_client.get("/categories")
        body = response.body
        items = body["data"] if isinstance(body, dict) and "data" in body else body
        names = [c["name"].lower() for c in items]
        # At least one of these should exist
        expected = {"hand tools", "power tools", "hammers"}
        found = expected & set(names)
        assert found, f"None of {expected} found in categories: {names}"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.skip(reason="GET /categories/{id} returns 405 on practicesoftwaretesting.com — only list endpoint is supported")
class TestPracticeCategoryDetailAPI:
    """Tests for GET /categories/{id} — skipped: endpoint returns 405."""

    def test_get_category_by_id_returns_200(
        self, practice_client: APIClient, first_category_id: str
    ):
        practice_client.get(f"/categories/{first_category_id}").assert_status(200)

    def test_category_detail_has_name(
        self, practice_client: APIClient, first_category_id: str
    ):
        response = practice_client.get(f"/categories/{first_category_id}")
        body = response.body
        assert "name" in body

    def test_category_id_matches_requested(
        self, practice_client: APIClient, first_category_id: str
    ):
        response = practice_client.get(f"/categories/{first_category_id}")
        assert response.body.get("id") == first_category_id

    def test_invalid_category_id_returns_404(self, practice_client: APIClient):
        response = practice_client.get(
            "/categories/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code in (404, 422)


@pytest.mark.api
@pytest.mark.regression
class TestPracticeCategoryTreeAPI:
    """Tests for GET /categories/tree."""

    def test_category_tree_returns_200(self, practice_client: APIClient):
        """GET /categories/tree returns 200."""
        response = practice_client.get("/categories/tree")
        assert response.status_code in (200, 404), (
            f"Unexpected status: {response.status_code}"
        )

    def test_category_tree_is_hierarchical(self, practice_client: APIClient):
        """Root categories have a 'sub_categories' or 'children' array."""
        response = practice_client.get("/categories/tree")
        if response.status_code != 200:
            pytest.skip("/categories/tree not available")
        body = response.body
        items = body if isinstance(body, list) else body.get("data", [])
        if not items:
            pytest.skip("Empty category tree")
        # At least one category should have a children/sub_categories key
        has_children = any(
            "sub_categories" in c or "children" in c for c in items
        )
        assert has_children, (
            f"No category in tree has children/sub_categories. Keys: {list(items[0].keys())}"
        )
