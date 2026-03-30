"""
UI Tests: Practice Software Testing — Product Detail Page
Covers: page load, price format, add to cart, quantity controls, breadcrumb.
"""
import pytest
from playwright.sync_api import Page

from pages.practice_home_page import PracticeHomePage
from pages.practice_product_page import PracticeProductPage
from pages.practice_cart_page import PracticeCartPage
from test_data.practice_test_data import PRODUCT_SEARCH_QUERY


@pytest.mark.ui
@pytest.mark.smoke
class TestPracticeProductDetail:
    """Smoke tests for the product detail page."""

    def test_product_page_loads_from_homepage(self, page: Page):
        """Clicking a product on the homepage opens its detail page."""
        home = PracticeHomePage(page)
        home.open()
        home.click_product_by_index(0)

        product = PracticeProductPage(page)
        product.assert_loaded()
        assert "/product/" in page.url, f"Expected /product/ in URL, got: {page.url}"

    def test_product_name_displayed(self, page: Page):
        """Product name is visible on the detail page."""
        home = PracticeHomePage(page)
        home.open()
        home.click_product_by_index(0)
        product = PracticeProductPage(page)
        name = product.get_product_name()
        assert len(name) > 0, "Product name is empty"

    def test_product_price_format(self, page: Page):
        """Product price starts with '$'."""
        home = PracticeHomePage(page)
        home.open()
        home.click_product_by_index(0)
        product = PracticeProductPage(page)
        product.assert_price_format()

    def test_add_to_cart_button_enabled(self, page: Page):
        """'Add to cart' button is enabled for an in-stock product."""
        home = PracticeHomePage(page)
        home.open()
        home.click_product_by_index(0)
        product = PracticeProductPage(page)
        assert product.is_add_to_cart_enabled(), "Add to cart button is disabled"


@pytest.mark.ui
@pytest.mark.regression
class TestPracticeAddToCart:
    """Tests for adding products to the cart from the detail page."""

    def test_add_single_item_to_cart(self, page: Page):
        """Adding 1 item to cart shows a success confirmation."""
        home = PracticeHomePage(page)
        home.open()
        home.click_product_by_index(0)

        product = PracticeProductPage(page)
        product.add_to_cart()
        product.assert_add_to_cart_success()

    def test_add_multiple_quantity_to_cart(self, page: Page):
        """Changing quantity to 3 and adding to cart succeeds."""
        home = PracticeHomePage(page)
        home.open()
        home.click_product_by_index(0)

        product = PracticeProductPage(page)
        product.set_quantity(3)
        assert product.get_quantity() == 3
        product.add_to_cart()
        product.assert_add_to_cart_success()

    def test_add_to_cart_updates_cart_badge(self, page: Page):
        """Cart badge count increases after adding a product."""
        home = PracticeHomePage(page)
        home.open()
        home.click_product_by_index(0)

        product = PracticeProductPage(page)
        product.add_to_cart()
        # Cart badge should show at least 1
        product.assert_cart_count_updated(1)

    def test_product_in_cart_after_add(self, page: Page):
        """After adding a product, it appears in the cart."""
        home = PracticeHomePage(page)
        home.open()
        home.click_product_by_index(0)

        product = PracticeProductPage(page)
        product_name = product.get_product_name()
        product.add_to_cart()

        # Navigate to cart and verify
        cart = PracticeCartPage(page)
        cart.open_via_navbar()
        cart.assert_item_in_cart(product_name)

    def test_add_two_different_products(self, page: Page):
        """Adding two different products results in 2 cart items."""
        home = PracticeHomePage(page)
        home.open()

        # Add first product
        home.click_product_by_index(0)
        PracticeProductPage(page).add_to_cart()

        # Back to home and add second product
        page.go_back()
        page.wait_for_load_state("networkidle")
        home.click_product_by_index(1)
        PracticeProductPage(page).add_to_cart()

        # Verify cart has 2 items
        cart = PracticeCartPage(page)
        cart.open_via_navbar()
        assert cart.get_item_count() >= 2


@pytest.mark.ui
@pytest.mark.regression
class TestPracticeProductSearch:
    """Tests combining search + product detail navigation."""

    def test_search_and_open_product(self, page: Page):
        """Search for a term, open the first result, and verify product page."""
        home = PracticeHomePage(page)
        home.open()
        home.search(PRODUCT_SEARCH_QUERY)
        count = home.get_product_count()
        if count == 0:
            pytest.skip("Search returned no results")
        home.click_product_by_index(0)
        product = PracticeProductPage(page)
        product.assert_loaded()

    def test_breadcrumb_reflects_navigation(self, page: Page):
        """Breadcrumb on product page shows at least 2 levels."""
        home = PracticeHomePage(page)
        home.open()
        home.click_product_by_index(0)
        product = PracticeProductPage(page)
        breadcrumbs = product.get_breadcrumb_items()
        assert len(breadcrumbs) >= 2, f"Expected 2+ breadcrumb items, got: {breadcrumbs}"
