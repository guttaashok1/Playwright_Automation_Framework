"""
Page Object: Practice Software Testing — Auth Pages (Login & Register)
URLs:
  Login:    https://practicesoftwaretesting.com/auth/login
  Register: https://practicesoftwaretesting.com/auth/register

Locator priority: get_by_role → get_by_label → get_by_placeholder
                  → get_by_text → get_by_test_id → locator
"""
from __future__ import annotations

from loguru import logger
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class PracticeLoginPage(BasePage):
    """Login page for practicesoftwaretesting.com."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.url = "https://practicesoftwaretesting.com/auth/login"

    # ── Navigation ────────────────────────────────────────────────────────────

    def open(self) -> "PracticeLoginPage":
        logger.info("[LoginPage] Opening login page")
        self.navigate_to_url(self.url)
        self.wait_for_network_idle()
        return self

    # ── Locators ─────────────────────────────────────────────────────────────

    def _email_input(self):
        # get_by_placeholder → get_by_test_id
        loc = self.page.get_by_placeholder("Your email")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("email")

    def _password_input(self):
        # get_by_placeholder → get_by_test_id
        loc = self.page.get_by_placeholder("Your password")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("password")

    def _login_button(self):
        # get_by_role (highest priority for buttons)
        return self.page.get_by_role("button", name="Login")

    def _error_message(self):
        # get_by_test_id → locator
        loc = self.page.get_by_test_id("login-error")
        if loc.count() > 0:
            return loc
        return self.page.locator(".alert-danger, [class*='error']")

    def _nav_user_menu(self):
        # get_by_test_id
        return self.page.get_by_test_id("nav-menu")

    def _sign_out_link(self):
        # get_by_role → get_by_test_id
        loc = self.page.get_by_role("link", name="Sign out")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("nav-sign-out")

    def _register_link(self):
        # get_by_role → get_by_test_id
        loc = self.page.get_by_role("link", name="Register")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("register-link")

    def _forgot_password_link(self):
        # get_by_role → get_by_text → get_by_test_id
        loc = self.page.get_by_role("link", name="Forgot")
        if loc.count() > 0:
            return loc
        loc = self.page.get_by_text("Forgot password")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("forgot-password-link")

    # ── Actions ───────────────────────────────────────────────────────────────

    def enter_email(self, email: str) -> None:
        loc = self._email_input()
        loc.clear()
        loc.fill(email)

    def enter_password(self, password: str) -> None:
        loc = self._password_input()
        loc.clear()
        loc.fill(password)

    def click_login(self) -> None:
        self._login_button().click()
        self.wait_for_network_idle()

    def login(self, email: str, password: str) -> None:
        logger.info(f"[LoginPage] Logging in as {email}")
        self.enter_email(email)
        self.enter_password(password)
        self.click_login()

    def click_register_link(self) -> None:
        self._register_link().click()
        self.wait_for_network_idle()

    def click_forgot_password(self) -> None:
        self._forgot_password_link().click()
        self.wait_for_network_idle()

    def logout(self) -> None:
        logger.info("[LoginPage] Logging out")
        self._nav_user_menu().click()
        self._sign_out_link().click()
        self.wait_for_network_idle()

    # ── Getters ───────────────────────────────────────────────────────────────

    def get_error_message(self) -> str:
        loc = self._error_message()
        if loc.is_visible():
            return loc.inner_text()
        return ""

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_login_form_visible(self) -> None:
        expect(self._email_input()).to_be_visible()
        expect(self._password_input()).to_be_visible()
        expect(self._login_button()).to_be_visible()

    def assert_error_visible(self) -> None:
        expect(self._error_message()).to_be_visible()

    def assert_logged_in(self) -> None:
        """After successful login the user is on /account."""
        self.assert_url_contains("/account")

    def assert_still_on_login(self) -> None:
        self.assert_url_contains("/auth/login")

    def assert_email_error(self) -> None:
        loc = self.page.get_by_test_id("email-error")
        if loc.count() == 0:
            loc = self.page.locator(".invalid-feedback, [id*='email'][class*='error']")
        expect(loc).to_be_visible()

    def assert_password_error(self) -> None:
        loc = self.page.get_by_test_id("password-error")
        if loc.count() == 0:
            loc = self.page.locator(".invalid-feedback, [id*='password'][class*='error']")
        expect(loc).to_be_visible()


class PracticeRegisterPage(BasePage):
    """Registration page for practicesoftwaretesting.com."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.url = "https://practicesoftwaretesting.com/auth/register"

    # ── Navigation ────────────────────────────────────────────────────────────

    def open(self) -> "PracticeRegisterPage":
        logger.info("[RegisterPage] Opening registration page")
        self.navigate_to_url(self.url)
        self.wait_for_network_idle()
        return self

    # ── Form Filling ──────────────────────────────────────────────────────────

    def fill_registration_form(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        dob: str = "1990-01-15",
        street: str = "123 Test Street",
        postcode: str = "10001",
        city: str = "New York",
        state: str = "NY",
        country: str = "US",
        phone: str = "1234567890",
    ) -> None:
        logger.info(f"[RegisterPage] Filling form for {email}")
        page = self.page
        # get_by_placeholder (highest applicable priority for unlabelled inputs)
        page.get_by_placeholder("First name *").fill(first_name)
        page.get_by_placeholder("Your last name *").fill(last_name)
        page.get_by_placeholder("YYYY-MM-DD").fill(dob)
        page.get_by_placeholder("Your Street *").fill(street)
        page.get_by_placeholder("Your Postcode *").fill(postcode)
        page.get_by_placeholder("Your City *").fill(city)
        page.get_by_placeholder("Your State *").fill(state)
        # get_by_role for the country select (combobox)
        country_sel = page.get_by_role("combobox")
        if country_sel.count() > 0:
            country_sel.first.select_option(value=country)
        else:
            page.locator("select").select_option(value=country)
        page.get_by_placeholder("Your phone *").fill(phone)
        page.get_by_placeholder("Your email *").fill(email)
        page.get_by_placeholder("Your password").fill(password)

    def submit(self) -> None:
        logger.info("[RegisterPage] Submitting registration form")
        # get_by_role — highest priority for buttons
        self.page.get_by_role("button", name="Register").click()
        self.wait_for_network_idle(timeout=20_000)

    def register(self, first_name: str, last_name: str, email: str, password: str, **kwargs) -> None:
        self.fill_registration_form(first_name, last_name, email, password, **kwargs)
        self.submit()

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_form_visible(self) -> None:
        self.assert_url_contains("/auth/register")

    def assert_registration_success(self) -> None:
        """After registration, site redirects to login."""
        self.assert_url_contains("/auth/login")

    def assert_form_error_visible(self) -> None:
        loc = self.page.get_by_test_id("register-error")
        if loc.count() == 0:
            loc = self.page.locator(".alert-danger, .invalid-feedback")
        expect(loc).to_be_visible()
