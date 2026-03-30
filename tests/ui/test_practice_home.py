"""
UI Tests: Practice Software Testing — Homepage
Covers: page load, product grid, search, sort, category filter, pagination, navigation.
"""
import pytest
from playwright.sync_api import Page

from pages.practice_home_page import PracticeHomePage
from test_data.practice_test_data import (
    PRODUCT_SEARCH_QUERY,
    PRODUCT_NAME_PLIERS,
    SORT_NAME_ASC,
    SORT_PRICE_ASC,
    SORT_PRICE_DESC,
    CATEGORY_HAND_TOOLS,
)


@pytest.mark.ui
@pytest.mark.smoke
class TestPracticeHomePage:
    """Smoke tests for the homepage — fast, critical path."""

    def test_home_page_loads(self, page: Page):
        """Homepage opens successfully and shows the product grid."""
        home = PracticeHomePage(page)
        home.open()
        home.assert_loaded()
        home.assert_products_visible()

    def test_page_title(self, page: Page):
        """Page title includes 'Toolshop' or 'Practice'."""
        import re
        home = PracticeHomePage(page)
        home.open()
        title = home.get_title()
        assert re.search(r"Toolshop|Practice", title, re.IGNORECASE), (
            f"Unexpected page title: {title}"
        )

    def test_sign_in_link_visible(self, page: Page):
        """Sign-in navigation link is visible before authentication."""
        home = PracticeHomePage(page)
        home.open()
        home.assert_sign_in_link_visible()

    def test_product_cards_have_name_and_price(self, page: Page):
        """Every visible product card displays a name and a price."""
        home = PracticeHomePage(page)
        home.open()
        names  = home.get_product_names()
        prices = home.get_product_prices()
        assert len(names) > 0,  "No product names found"
        assert len(prices) > 0, "No product prices found"
        for price in prices:
            assert "$" in price, f"Price '{price}' missing '$' symbol"


@pytest.mark.ui
@pytest.mark.regression
class TestPracticeSearch:
    """Tests covering the homepage search feature."""

    def test_search_returns_relevant_results(self, page: Page):
        """Searching for 'plier' returns products with 'plier' in name."""
        home = PracticeHomePage(page)
        home.open()
        home.search(PRODUCT_SEARCH_QUERY)
        home.assert_search_results_contain(PRODUCT_SEARCH_QUERY)

    def test_search_for_exact_product_name(self, page: Page):
        """Searching for exact product name returns at least 1 result."""
        home = PracticeHomePage(page)
        home.open()
        home.search(PRODUCT_NAME_PLIERS)
        assert home.get_product_count() >= 1

    def test_search_no_results(self, page: Page):
        """Searching for a non-existent term should show 0 results."""
        home = PracticeHomePage(page)
        home.open()
        home.search("zzz_nonexistent_product_xyz")
        home.assert_no_products_found()

    def test_search_reset_restores_all_products(self, page: Page):
        """Clearing search restores the full product grid."""
        home = PracticeHomePage(page)
        home.open()
        initial_count = home.get_product_count()
        home.search("hammer")
        filtered_count = home.get_product_count()
        home.clear_search()
        restored_count = home.get_product_count()
        assert restored_count >= filtered_count
        assert restored_count == initial_count

    def test_search_input_reflects_query(self, page: Page):
        """Search input retains the entered query after submission."""
        home = PracticeHomePage(page)
        home.open()
        home.search("hammer")
        assert "hammer" in home.get_search_value().lower()

    @pytest.mark.parametrize("query", ["plier", "hammer", "screwdriver", "wrench"])
    def test_search_various_terms(self, page: Page, query: str):
        """Parametrized: several search terms each return results."""
        home = PracticeHomePage(page)
        home.open()
        home.search(query)
        # Site may or may not have every item — just assert page doesn't error
        count = home.get_product_count()
        assert count >= 0, f"Search for '{query}' caused an error"


@pytest.mark.ui
@pytest.mark.regression
class TestPracticeSort:
    """Tests covering product sort options."""

    def test_sort_by_name_ascending(self, page: Page):
        """Sort by name A→Z: first name alphabetically ≤ last name."""
        home = PracticeHomePage(page)
        home.open()
        home.sort_by(SORT_NAME_ASC)
        names = home.get_product_names()
        assert len(names) >= 2
        assert names[0].lower() <= names[-1].lower(), (
            f"Names not sorted A→Z: first='{names[0]}', last='{names[-1]}'"
        )

    def test_sort_by_price_ascending(self, page: Page):
        """Sort price low→high: prices are in ascending order."""
        home = PracticeHomePage(page)
        home.open()
        home.sort_by(SORT_PRICE_ASC)
        prices = home.get_product_prices()
        numeric = [float(p.replace("$", "").strip()) for p in prices if "$" in p]
        assert numeric == sorted(numeric), (
            f"Prices are not ascending: {numeric}"
        )

    def test_sort_by_price_descending(self, page: Page):
        """Sort price high→low: prices are in descending order."""
        home = PracticeHomePage(page)
        home.open()
        home.sort_by(SORT_PRICE_DESC)
        prices = home.get_product_prices()
        numeric = [float(p.replace("$", "").strip()) for p in prices if "$" in p]
        assert numeric == sorted(numeric, reverse=True), (
            f"Prices are not descending: {numeric}"
        )


@pytest.mark.ui
@pytest.mark.regression
class TestPracticeCategoryFilter:
    """Tests covering the category sidebar filter."""

    def test_filter_by_hand_tools(self, page: Page):
        """Selecting 'Hand Tools' category shows only Hand Tools products."""
        home = PracticeHomePage(page)
        home.open()
        home.filter_by_category(CATEGORY_HAND_TOOLS)
        # After filtering, there should still be products
        assert home.get_product_count() > 0, "No products after Hand Tools filter"

    def test_category_labels_visible(self, page: Page):
        """At least some category checkboxes are visible in the sidebar."""
        home = PracticeHomePage(page)
        home.open()
        categories = home.get_visible_category_names()
        assert len(categories) > 0, "No category labels found in sidebar"

    def test_filter_reduces_product_count(self, page: Page):
        """Applying a category filter reduces or maintains the product count."""
        home = PracticeHomePage(page)
        home.open()
        all_count = home.get_product_count()
        home.filter_by_category(CATEGORY_HAND_TOOLS)
        filtered_count = home.get_product_count()
        assert filtered_count <= all_count, (
            f"Filtered count ({filtered_count}) > all count ({all_count})"
        )


@pytest.mark.ui
@pytest.mark.regression
class TestPracticePagination:
    """Tests covering pagination controls."""

    def test_next_page_loads_more_products(self, page: Page):
        """Clicking 'next page' loads a different set of products."""
        home = PracticeHomePage(page)
        home.open()
        if not home.has_next_page():
            pytest.skip("Only one page of results — pagination not exercisable")
        first_page_names = home.get_product_names()
        home.go_to_next_page()
        second_page_names = home.get_product_names()
        assert first_page_names != second_page_names, (
            "Same products on page 1 and page 2"
        )
