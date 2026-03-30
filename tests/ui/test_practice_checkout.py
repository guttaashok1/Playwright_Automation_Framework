"""
UI Tests: Practice Software Testing — End-to-End Checkout Flow
Covers: cart → login → billing → payment → confirmation.
"""
import pytest
from playwright.sync_api import Page

from pages.practice_home_page import PracticeHomePage
from pages.practice_product_page import PracticeProductPage
from pages.practice_cart_page import PracticeCartPage
from pages.practice_checkout_page import PracticeCheckoutPage
from pages.practice_auth_page import PracticeLoginPage
from test_data.practice_test_data import (
    CUSTOMER_EMAIL,
    CUSTOMER_PASSWORD,
    BASE_URL,
    make_billing,
)


def _add_product_and_go_to_cart(page: Page) -> None:
    """Helper: add first product to cart then navigate to cart page."""
    home = PracticeHomePage(page)
    home.navigate_to_url(BASE_URL)
    home.wait_for_network_idle()
    home.click_product_by_index(0)
    PracticeProductPage(page).add_to_cart()
    PracticeCartPage(page).open_via_navbar()


@pytest.mark.ui
@pytest.mark.smoke
class TestPracticeCheckoutSmoke:
    """Smoke tests for the checkout flow."""

    def test_proceed_button_visible_with_items_in_cart(self, page: Page):
        """Cart with items shows the 'Proceed to Checkout' button."""
        _add_product_and_go_to_cart(page)
        cart = PracticeCartPage(page)
        cart.assert_proceed_button_visible()

    def test_proceed_from_cart_advances_checkout(self, page: Page):
        """Clicking Proceed from cart advances to the next checkout step."""
        _add_product_and_go_to_cart(page)
        checkout = PracticeCheckoutPage(page)
        checkout.proceed_from_cart()
        # Should have moved past step 1
        assert "/checkout" in page.url


@pytest.mark.ui
@pytest.mark.regression
class TestPracticeCheckoutAuthenticated:
    """Full checkout tests using the seeded customer account."""

    def test_checkout_login_step(self, page: Page):
        """Checkout login step authenticates the user successfully."""
        _add_product_and_go_to_cart(page)
        checkout = PracticeCheckoutPage(page)
        checkout.proceed_from_cart()
        checkout.login_at_checkout(CUSTOMER_EMAIL, CUSTOMER_PASSWORD)
        # After login, billing step should be reachable
        assert "/checkout" in page.url

    def test_billing_step_accepts_valid_data(self, page: Page):
        """Billing form accepts valid address data."""
        _add_product_and_go_to_cart(page)
        checkout = PracticeCheckoutPage(page)
        checkout.proceed_from_cart()
        checkout.login_at_checkout(CUSTOMER_EMAIL, CUSTOMER_PASSWORD)
        billing = make_billing()
        checkout.fill_billing(**billing)
        checkout.proceed_from_billing()
        assert "/checkout" in page.url

    def test_payment_step_visible_after_billing(self, page: Page):
        """After billing, the payment step is accessible."""
        _add_product_and_go_to_cart(page)
        checkout = PracticeCheckoutPage(page)
        checkout.proceed_from_cart()
        checkout.login_at_checkout(CUSTOMER_EMAIL, CUSTOMER_PASSWORD)
        checkout.fill_billing(**make_billing())
        checkout.proceed_from_billing()
        # Payment method selector or confirm button should be visible
        assert checkout._confirm_order_btn().is_visible() or \
               checkout._payment_method().is_visible(), \
               "Neither payment method nor confirm button is visible"

    @pytest.mark.slow
    def test_full_checkout_flow(self, page: Page):
        """
        Complete end-to-end checkout: product → cart → login → billing → payment → confirm.
        Verifies order confirmation is displayed.
        """
        # Pre-login to avoid issues with checkout login step
        login = PracticeLoginPage(page)
        login.open()
        login.login(CUSTOMER_EMAIL, CUSTOMER_PASSWORD)
        login.assert_logged_in()

        # Add product to cart
        home = PracticeHomePage(page)
        home.navigate_to_url(BASE_URL)
        home.wait_for_network_idle()
        home.click_product_by_index(0)
        PracticeProductPage(page).add_to_cart()

        # Cart
        cart = PracticeCartPage(page)
        cart.open_via_navbar()
        cart.assert_cart_not_empty()
        cart.proceed_to_checkout()

        # Checkout
        checkout = PracticeCheckoutPage(page)
        if checkout._login_email().is_visible():
            checkout.login_at_checkout(CUSTOMER_EMAIL, CUSTOMER_PASSWORD)

        checkout.fill_billing(**make_billing())
        checkout.proceed_from_billing()
        checkout.select_payment_method()
        checkout.fill_bank_transfer()
        checkout.confirm_order()

        checkout.assert_order_confirmed()


@pytest.mark.ui
@pytest.mark.regression
class TestPracticeCheckoutValidation:
    """Negative tests for checkout validation."""

    def test_empty_cart_proceed_is_not_available(self, page: Page):
        """
        An empty cart either disables/hides the Proceed button or shows a message.
        """
        cart = PracticeCartPage(page)
        cart.open()
        if not cart.is_empty():
            cart.clear_cart()
        # Proceed button should not be visible for empty cart
        assert not cart._proceed_to_checkout_btn().is_visible(), (
            "Proceed button is visible for an empty cart"
        )
