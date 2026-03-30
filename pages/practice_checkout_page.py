"""
Page Object: Practice Software Testing — Checkout Flow
Steps:
  1. Cart review  (/checkout)
  2. Sign-in gate (/checkout step 2)
  3. Billing info  (/checkout step 3)
  4. Payment       (/checkout step 4)
  5. Confirmation  (/checkout/confirmation)

Locator priority: get_by_role → get_by_label → get_by_placeholder
                  → get_by_text → get_by_test_id → locator
"""
from __future__ import annotations

from loguru import logger
from playwright.sync_api import expect

from pages.base_page import BasePage


class PracticeCheckoutPage(BasePage):
    """Multi-step checkout page for practicesoftwaretesting.com."""

    BASE = "https://practicesoftwaretesting.com"

    # ── Locators: Step 1 — Cart ───────────────────────────────────────────────

    def _proceed_step1(self):
        # get_by_role button → get_by_test_id
        loc = self.page.get_by_role("button", name="Proceed to checkout")
        if loc.count() > 0:
            return loc
        loc = self.page.get_by_role("link", name="Proceed to checkout")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("proceed-1")

    # ── Locators: Step 2 — Sign In ────────────────────────────────────────────

    def _login_email(self):
        # get_by_label → get_by_placeholder → get_by_test_id
        loc = self.page.get_by_label("Email")
        if loc.count() > 0:
            return loc
        loc = self.page.get_by_placeholder("Your email")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("email")

    def _login_password(self):
        # get_by_label → get_by_placeholder → get_by_test_id
        loc = self.page.get_by_label("Password")
        if loc.count() > 0:
            return loc
        loc = self.page.get_by_placeholder("Your password")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("password")

    def _login_submit(self):
        # get_by_role button
        loc = self.page.get_by_role("button", name="Login")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("login-submit")

    def _proceed_step2(self):
        # get_by_role → get_by_test_id
        loc = self.page.get_by_role("button", name="Proceed")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("proceed-2")

    # ── Locators: Step 3 — Billing ────────────────────────────────────────────

    def _billing_first_name(self):
        # get_by_label → get_by_placeholder → get_by_test_id
        loc = self.page.get_by_label("First name")
        if loc.count() > 0:
            return loc
        loc = self.page.get_by_placeholder("First name")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("first-name")

    def _billing_last_name(self):
        loc = self.page.get_by_label("Last name")
        if loc.count() > 0:
            return loc
        loc = self.page.get_by_placeholder("Last name")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("last-name")

    def _billing_address(self):
        loc = self.page.get_by_label("Address")
        if loc.count() > 0:
            return loc
        loc = self.page.get_by_placeholder("Address")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("address")

    def _billing_city(self):
        loc = self.page.get_by_label("City")
        if loc.count() > 0:
            return loc
        loc = self.page.get_by_placeholder("City")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("city")

    def _billing_state(self):
        loc = self.page.get_by_label("State")
        if loc.count() > 0:
            return loc
        loc = self.page.get_by_placeholder("State")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("state")

    def _billing_postcode(self):
        loc = self.page.get_by_label("Postcode")
        if loc.count() > 0:
            return loc
        loc = self.page.get_by_placeholder("Postcode")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("postcode")

    def _billing_country(self):
        # get_by_label → get_by_test_id
        loc = self.page.get_by_label("Country")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("country")

    def _billing_phone(self):
        loc = self.page.get_by_label("Phone")
        if loc.count() > 0:
            return loc
        loc = self.page.get_by_placeholder("Phone")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("phone")

    def _billing_email(self):
        loc = self.page.get_by_label("Email")
        if loc.count() > 0:
            return loc
        loc = self.page.get_by_placeholder("Email")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("email")

    def _proceed_step3(self):
        loc = self.page.get_by_role("button", name="Proceed")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("proceed-3")

    # ── Locators: Step 4 — Payment ────────────────────────────────────────────

    def _payment_method(self):
        # get_by_label → get_by_test_id
        loc = self.page.get_by_label("Payment Method")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("payment-method")

    def _payment_bank_name(self):
        loc = self.page.get_by_label("Bank Name")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("bank-name")

    def _payment_account_number(self):
        loc = self.page.get_by_label("Account Number")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("account-number")

    def _payment_account_name(self):
        loc = self.page.get_by_label("Account Name")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("account-name")

    def _confirm_order_btn(self):
        # get_by_role button → get_by_test_id
        loc = self.page.get_by_role("button", name="Confirm")
        if loc.count() > 0:
            return loc
        loc = self.page.get_by_role("button", name="Place Order")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("finish")

    # ── Locators: Confirmation ────────────────────────────────────────────────

    def _order_confirmation(self):
        loc = self.page.get_by_test_id("order-confirmation")
        if loc.count() > 0:
            return loc
        return self.page.locator(".alert-success")

    def _order_number(self):
        loc = self.page.get_by_test_id("order-number")
        if loc.count() > 0:
            return loc
        return self.page.locator(".alert-success")

    # ── Step 1: Cart → Proceed ────────────────────────────────────────────────

    def open_cart(self) -> "PracticeCheckoutPage":
        self.navigate_to_url(f"{self.BASE}/checkout")
        self.wait_for_network_idle()
        return self

    def proceed_from_cart(self) -> "PracticeCheckoutPage":
        logger.info("[Checkout] Step 1 → Proceed from cart")
        self._proceed_step1().click()
        self.wait_for_network_idle()
        return self

    # ── Step 2: Login During Checkout ─────────────────────────────────────────

    def login_at_checkout(self, email: str, password: str) -> "PracticeCheckoutPage":
        logger.info(f"[Checkout] Step 2 → Logging in as {email}")
        if self._login_email().is_visible():
            self._login_email().fill(email)
            self._login_password().fill(password)
            self._login_submit().click()
            self.wait_for_network_idle()
        else:
            logger.info("[Checkout] Already authenticated, skipping login step")
        return self

    def proceed_as_guest(self) -> "PracticeCheckoutPage":
        self._proceed_step2().click()
        self.wait_for_network_idle()
        return self

    # ── Step 3: Billing ───────────────────────────────────────────────────────

    def fill_billing(
        self,
        first_name: str = "John",
        last_name: str = "Doe",
        address: str = "123 Test Ave",
        city: str = "New York",
        state: str = "NY",
        postcode: str = "10001",
        country: str = "US",
        phone: str = "5551234567",
        email: str = "test@example.com",
    ) -> "PracticeCheckoutPage":
        logger.info("[Checkout] Step 3 → Filling billing details")
        fields = [
            (self._billing_first_name, first_name),
            (self._billing_last_name, last_name),
            (self._billing_address, address),
            (self._billing_city, city),
            (self._billing_state, state),
            (self._billing_postcode, postcode),
            (self._billing_phone, phone),
            (self._billing_email, email),
        ]
        for locator_fn, value in fields:
            loc = locator_fn()
            if loc.is_visible():
                loc.clear()
                loc.fill(value)

        country_loc = self._billing_country()
        if country_loc.is_visible():
            country_loc.select_option(country)
        return self

    def proceed_from_billing(self) -> "PracticeCheckoutPage":
        self._proceed_step3().click()
        self.wait_for_network_idle()
        return self

    # ── Step 4: Payment ───────────────────────────────────────────────────────

    def select_payment_method(self, method: str = "Bank Transfer") -> "PracticeCheckoutPage":
        logger.info(f"[Checkout] Step 4 → Selecting payment: {method}")
        loc = self._payment_method()
        if loc.is_visible():
            loc.select_option(method)
        return self

    def fill_bank_transfer(
        self,
        bank_name: str = "Test Bank",
        account_number: str = "1234567890",
        account_name: str = "John Doe",
    ) -> "PracticeCheckoutPage":
        bank_loc = self._payment_bank_name()
        if bank_loc.is_visible():
            bank_loc.fill(bank_name)
        acc_num_loc = self._payment_account_number()
        if acc_num_loc.is_visible():
            acc_num_loc.fill(account_number)
        acc_name_loc = self._payment_account_name()
        if acc_name_loc.is_visible():
            acc_name_loc.fill(account_name)
        return self

    def confirm_order(self) -> "PracticeCheckoutPage":
        logger.info("[Checkout] Confirming order")
        self._confirm_order_btn().click()
        self.wait_for_network_idle(timeout=30_000)
        return self

    # ── Convenience: Full Flow ────────────────────────────────────────────────

    def complete_checkout_authenticated(
        self,
        email: str,
        password: str,
        billing: dict | None = None,
    ) -> str:
        """
        Run the full checkout as an authenticated user.
        Returns the order/invoice number from the confirmation page.
        """
        billing = billing or {}
        self.proceed_from_cart()
        self.login_at_checkout(email, password)
        self.fill_billing(**billing)
        self.proceed_from_billing()
        self.select_payment_method()
        self.fill_bank_transfer()
        self.confirm_order()
        return self.get_order_number()

    # ── Confirmation ─────────────────────────────────────────────────────────

    def get_order_number(self) -> str:
        order_num = self.page.get_by_test_id("order-number")
        if order_num.is_visible():
            return order_num.inner_text()
        invoice = self.page.locator(".alert-success")
        if invoice.is_visible():
            return invoice.inner_text()
        return ""

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_on_checkout(self) -> None:
        self.assert_url_contains("/checkout")

    def assert_order_confirmed(self) -> None:
        """Assert the order confirmation message is visible."""
        expect(
            self._order_confirmation().or_(
                self.page.locator(".alert-success")
            )
        ).to_be_visible(timeout=15_000)

    def assert_step(self, step_number: int) -> None:
        self.assert_url_contains(f"step={step_number}")
