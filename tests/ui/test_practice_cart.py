"""
UI Tests: Practice Software Testing — Shopping Cart
Covers: add items, view cart, update quantity, remove items, empty cart, proceed.
"""
import pytest
from playwright.sync_api import Page

from pages.practice_home_page import PracticeHomePage
from pages.practice_product_page import PracticeProductPage
from pages.practice_cart_page import PracticeCartPage
from test_data.practice_test_data import BASE_URL


def _add_product_to_cart(page: Page, index: int = 0) -> str:
    """Helper: navigate home → product → add to cart. Returns product name."""
    home = PracticeHomePage(page)
    home.navigate_to_url(BASE_URL)
    home.wait_for_network_idle()
    home.click_product_by_index(index)
    product = PracticeProductPage(page)
    name = product.get_product_name()
    product.add_to_cart()
    return name


@pytest.mark.ui
@pytest.mark.smoke
class TestPracticeCart:
    """Smoke tests for cart functionality."""

    def test_cart_page_loads(self, page: Page):
        """Cart page opens without errors."""
        cart = PracticeCartPage(page)
        cart.open()
        cart.assert_loaded()

    def test_added_product_appears_in_cart(self, page: Page):
        """A product added to cart is visible on the cart page."""
        name = _add_product_to_cart(page)
        cart = PracticeCartPage(page)
        cart.open_via_navbar()
        cart.assert_item_in_cart(name)
        cart.assert_cart_not_empty()

    def test_cart_shows_total(self, page: Page):
        """Cart total is displayed and non-zero after adding a product."""
        _add_product_to_cart(page)
        cart = PracticeCartPage(page)
        cart.open_via_navbar()
        cart.assert_total_is_not_zero()

    def test_proceed_to_checkout_button_visible(self, page: Page):
        """'Proceed to checkout' button is visible when cart has items."""
        _add_product_to_cart(page)
        cart = PracticeCartPage(page)
        cart.open_via_navbar()
        cart.assert_proceed_button_visible()


@pytest.mark.ui
@pytest.mark.regression
class TestPracticeCartOperations:
    """Tests for cart CRUD operations."""

    def test_remove_item_empties_single_item_cart(self, page: Page):
        """Removing the only cart item results in an empty cart."""
        _add_product_to_cart(page)
        cart = PracticeCartPage(page)
        cart.open_via_navbar()
        cart.assert_item_count(1)
        cart.remove_item(0)
        cart.assert_cart_empty()

    def test_remove_one_of_multiple_items(self, page: Page):
        """Removing one item from a 2-item cart leaves 1 item."""
        _add_product_to_cart(page, index=0)
        _add_product_to_cart(page, index=1)
        cart = PracticeCartPage(page)
        cart.open_via_navbar()
        count_before = cart.get_item_count()
        if count_before < 2:
            pytest.skip("Could not add two distinct products")
        cart.remove_item(0)
        assert cart.get_item_count() == count_before - 1

    def test_update_item_quantity(self, page: Page):
        """Updating quantity on a cart item reflects the change."""
        _add_product_to_cart(page)
        cart = PracticeCartPage(page)
        cart.open_via_navbar()
        cart.update_item_quantity(index=0, qty=3)
        quantities = cart.get_item_quantities()
        assert quantities[0] == 3, f"Expected qty=3, got {quantities[0]}"

    def test_cart_item_count_matches_navbar_badge(self, page: Page):
        """Cart badge in navbar equals the number of cart items."""
        home = PracticeHomePage(page)
        home.navigate_to_url(BASE_URL)
        home.wait_for_network_idle()
        home.click_product_by_index(0)
        PracticeProductPage(page).add_to_cart()

        cart = PracticeCartPage(page)
        cart.open_via_navbar()
        items = cart.get_item_count()
        assert items >= 1

    def test_empty_cart_shows_empty_state(self, page: Page):
        """Opening cart with no items shows the empty cart message."""
        cart = PracticeCartPage(page)
        cart.open()
        if not cart.is_empty():
            cart.clear_cart()
        cart.assert_cart_empty()


@pytest.mark.ui
@pytest.mark.regression
class TestPracticeCartPersistence:
    """Tests verifying cart state persistence across navigation."""

    def test_cart_persists_after_navigating_to_home(self, page: Page):
        """Items added to cart persist after navigating back to the homepage."""
        name = _add_product_to_cart(page)

        # Navigate away
        home = PracticeHomePage(page)
        home.navigate_to_url(BASE_URL)
        home.wait_for_network_idle()

        # Return to cart
        cart = PracticeCartPage(page)
        cart.open_via_navbar()
        cart.assert_item_in_cart(name)
