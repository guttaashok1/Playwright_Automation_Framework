"""
Page Object: Practice Software Testing — Checkout Flow
Steps:
  1. Cart review  (/checkout)
  2. Sign-in gate (/checkout step 2)
  3. Billing info  (/checkout step 3)
  4. Payment       (/checkout step 4)
  5. Confirmation  (/checkout/confirmation)
"""
from __future__ import annotations

from loguru import logger
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class PracticeCheckoutPage(BasePage):
    """Multi-step checkout page for practicesoftwaretesting.com."""

    BASE = "https://practicesoftwaretesting.com"

    # ── Step 1 — Cart ─────────────────────────────────────────────────────────
    _PROCEED_STEP1       = "[data-test='proceed-1']"

    # ── Step 2 — Sign In ──────────────────────────────────────────────────────
    _PROCEED_STEP2       = "[data-test='proceed-2']"
    _LOGIN_EMAIL         = "[data-test='email']"
    _LOGIN_PASSWORD      = "[data-test='password']"
    _LOGIN_SUBMIT        = "[data-test='login-submit']"

    # ── Step 3 — Billing ─────────────────────────────────────────────────────
    _BILLING_FIRST_NAME  = "[data-test='first-name']"
    _BILLING_LAST_NAME   = "[data-test='last-name']"
    _BILLING_ADDRESS     = "[data-test='address']"
    _BILLING_CITY        = "[data-test='city']"
    _BILLING_STATE       = "[data-test='state']"
    _BILLING_POSTCODE    = "[data-test='postcode']"
    _BILLING_COUNTRY     = "[data-test='country']"
    _BILLING_PHONE       = "[data-test='phone']"
    _BILLING_EMAIL       = "[data-test='email']"
    _PROCEED_STEP3       = "[data-test='proceed-3']"

    # ── Step 4 — Payment ─────────────────────────────────────────────────────
    _PAYMENT_METHOD      = "[data-test='payment-method']"
    _PAYMENT_BANK_NAME   = "[data-test='bank-name']"
    _PAYMENT_ACCOUNT_NUM = "[data-test='account-number']"
    _PAYMENT_ACCOUNT_NAME= "[data-test='account-name']"
    _CONFIRM_ORDER_BTN   = "[data-test='finish']"

    # ── Confirmation ─────────────────────────────────────────────────────────
    _ORDER_CONFIRMATION  = "[data-test='order-confirmation']"
    _ORDER_NUMBER        = "[data-test='order-number']"
    _INVOICE_NUMBER      = ".alert-success"

    # ── Generic ───────────────────────────────────────────────────────────────
    _STEP_INDICATOR      = ".step-indicator, .checkout-steps"
    _ERROR_TOAST         = ".toast-body"

    # ── Step 1: Cart → Proceed ────────────────────────────────────────────────

    def open_cart(self) -> "PracticeCheckoutPage":
        self.navigate_to_url(f"{self.BASE}/checkout")
        self.wait_for_network_idle()
        return self

    def proceed_from_cart(self) -> "PracticeCheckoutPage":
        logger.info("[Checkout] Step 1 → Proceed from cart")
        self.click(self._PROCEED_STEP1)
        self.wait_for_network_idle()
        return self

    # ── Step 2: Login During Checkout ─────────────────────────────────────────

    def login_at_checkout(self, email: str, password: str) -> "PracticeCheckoutPage":
        logger.info(f"[Checkout] Step 2 → Logging in as {email}")
        if self.is_visible(self._LOGIN_EMAIL):
            self.fill(self._LOGIN_EMAIL, email)
            self.fill(self._LOGIN_PASSWORD, password)
            self.click(self._LOGIN_SUBMIT)
            self.wait_for_network_idle()
        else:
            logger.info("[Checkout] Already authenticated, skipping login step")
        return self

    def proceed_as_guest(self) -> "PracticeCheckoutPage":
        self.click(self._PROCEED_STEP2)
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
        fields = {
            self._BILLING_FIRST_NAME: first_name,
            self._BILLING_LAST_NAME:  last_name,
            self._BILLING_ADDRESS:    address,
            self._BILLING_CITY:       city,
            self._BILLING_STATE:      state,
            self._BILLING_POSTCODE:   postcode,
            self._BILLING_PHONE:      phone,
            self._BILLING_EMAIL:      email,
        }
        for selector, value in fields.items():
            if self.is_visible(selector):
                self.fill(selector, value)

        if self.is_visible(self._BILLING_COUNTRY):
            self.select_option(self._BILLING_COUNTRY, country)
        return self

    def proceed_from_billing(self) -> "PracticeCheckoutPage":
        self.click(self._PROCEED_STEP3)
        self.wait_for_network_idle()
        return self

    # ── Step 4: Payment ───────────────────────────────────────────────────────

    def select_payment_method(self, method: str = "Bank Transfer") -> "PracticeCheckoutPage":
        logger.info(f"[Checkout] Step 4 → Selecting payment: {method}")
        if self.is_visible(self._PAYMENT_METHOD):
            self.select_option(self._PAYMENT_METHOD, method)
        return self

    def fill_bank_transfer(
        self,
        bank_name: str = "Test Bank",
        account_number: str = "1234567890",
        account_name: str = "John Doe",
    ) -> "PracticeCheckoutPage":
        if self.is_visible(self._PAYMENT_BANK_NAME):
            self.fill(self._PAYMENT_BANK_NAME, bank_name)
        if self.is_visible(self._PAYMENT_ACCOUNT_NUM):
            self.fill(self._PAYMENT_ACCOUNT_NUM, account_number)
        if self.is_visible(self._PAYMENT_ACCOUNT_NAME):
            self.fill(self._PAYMENT_ACCOUNT_NAME, account_name)
        return self

    def confirm_order(self) -> "PracticeCheckoutPage":
        logger.info("[Checkout] Confirming order")
        self.click(self._CONFIRM_ORDER_BTN)
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
        if self.is_visible(self._ORDER_NUMBER):
            return self.get_text(self._ORDER_NUMBER)
        if self.is_visible(self._INVOICE_NUMBER):
            return self.get_text(self._INVOICE_NUMBER)
        return ""

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_on_checkout(self) -> None:
        self.assert_url_contains("/checkout")

    def assert_order_confirmed(self) -> None:
        """Assert the order confirmation message is visible."""
        expect(
            self.page.locator(self._ORDER_CONFIRMATION).or_(
                self.page.locator(self._INVOICE_NUMBER)
            )
        ).to_be_visible(timeout=15_000)

    def assert_step(self, step_number: int) -> None:
        self.assert_url_contains(f"step={step_number}")
