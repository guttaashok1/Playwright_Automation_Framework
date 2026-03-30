"""
Page Object: Practice Software Testing — Auth Pages (Login & Register)
URLs:
  Login:    https://practicesoftwaretesting.com/auth/login
  Register: https://practicesoftwaretesting.com/auth/register
"""
from __future__ import annotations

from loguru import logger
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class PracticeLoginPage(BasePage):
    """Login page for practicesoftwaretesting.com."""

    # ── Selectors ────────────────────────────────────────────────────────────
    _EMAIL_INPUT       = "[data-test='email']"
    _PASSWORD_INPUT    = "[data-test='password']"
    _LOGIN_BUTTON      = "[data-test='login-submit']"
    _REGISTER_LINK     = "[data-test='register-link']"
    _FORGOT_PWD_LINK   = "[data-test='forgot-password-link']"
    _ERROR_MESSAGE     = "[data-test='login-error']"
    _EMAIL_ERROR       = "[data-test='email-error']"
    _PASSWORD_ERROR    = "[data-test='password-error']"
    _NAV_USER_MENU     = "[data-test='nav-menu']"
    _SIGN_OUT_LINK     = "[data-test='nav-sign-out']"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.url = "https://practicesoftwaretesting.com/auth/login"

    # ── Navigation ────────────────────────────────────────────────────────────

    def open(self) -> "PracticeLoginPage":
        logger.info("[LoginPage] Opening login page")
        self.navigate_to_url(self.url)
        self.wait_for_network_idle()
        return self

    # ── Actions ───────────────────────────────────────────────────────────────

    def enter_email(self, email: str) -> None:
        self.fill(self._EMAIL_INPUT, email)

    def enter_password(self, password: str) -> None:
        self.fill(self._PASSWORD_INPUT, password)

    def click_login(self) -> None:
        self.click(self._LOGIN_BUTTON)
        self.wait_for_network_idle()

    def login(self, email: str, password: str) -> None:
        logger.info(f"[LoginPage] Logging in as {email}")
        self.enter_email(email)
        self.enter_password(password)
        self.click_login()

    def click_register_link(self) -> None:
        self.click(self._REGISTER_LINK)
        self.wait_for_network_idle()

    def click_forgot_password(self) -> None:
        self.click(self._FORGOT_PWD_LINK)
        self.wait_for_network_idle()

    def logout(self) -> None:
        logger.info("[LoginPage] Logging out")
        self.click(self._NAV_USER_MENU)
        self.click(self._SIGN_OUT_LINK)
        self.wait_for_network_idle()

    # ── Getters ───────────────────────────────────────────────────────────────

    def get_error_message(self) -> str:
        if self.is_visible(self._ERROR_MESSAGE):
            return self.get_text(self._ERROR_MESSAGE)
        return ""

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_login_form_visible(self) -> None:
        self.assert_visible(self._EMAIL_INPUT)
        self.assert_visible(self._PASSWORD_INPUT)
        self.assert_visible(self._LOGIN_BUTTON)

    def assert_error_visible(self) -> None:
        self.assert_visible(self._ERROR_MESSAGE)

    def assert_logged_in(self) -> None:
        """After successful login the user is on /account."""
        self.assert_url_contains("/account")

    def assert_still_on_login(self) -> None:
        self.assert_url_contains("/auth/login")

    def assert_email_error(self) -> None:
        self.assert_visible(self._EMAIL_ERROR)

    def assert_password_error(self) -> None:
        self.assert_visible(self._PASSWORD_ERROR)


class PracticeRegisterPage(BasePage):
    """Registration page for practicesoftwaretesting.com."""

    # ── Selectors ────────────────────────────────────────────────────────────
    _FIRST_NAME       = "[data-test='first-name']"
    _LAST_NAME        = "[data-test='last-name']"
    _DOB              = "[data-test='dob']"
    _STREET           = "[data-test='street']"
    _POSTCODE         = "[data-test='postcode']"
    _CITY             = "[data-test='city']"
    _STATE            = "[data-test='state']"
    _COUNTRY          = "[data-test='country']"
    _PHONE            = "[data-test='phone']"
    _EMAIL            = "[data-test='email']"
    _PASSWORD         = "[data-test='password']"
    _REGISTER_BUTTON  = "[data-test='register-submit']"
    _FORM_ERROR       = "[data-test='register-error']"
    _LOGIN_LINK       = "[data-test='login-link']"

    # Fallback placeholder-based selectors (legacy)
    _FIRST_NAME_PH    = "input[placeholder='First name *']"
    _LAST_NAME_PH     = "input[placeholder='Your last name *']"
    _DOB_PH           = "input[placeholder='YYYY-MM-DD']"
    _STREET_PH        = "input[placeholder='Your Street *']"
    _POSTCODE_PH      = "input[placeholder='Your Postcode *']"
    _CITY_PH          = "input[placeholder='Your City *']"
    _STATE_PH         = "input[placeholder='Your State *']"
    _COUNTRY_SELECT   = "select"
    _PHONE_PH         = "input[placeholder='Your phone *']"
    _EMAIL_PH         = "input[placeholder='Your email *']"
    _PASSWORD_PH      = "input[placeholder='Your password']"
    _REGISTER_BTN     = "button[type='submit']"

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
        # Use placeholder-based selectors (more robust for this site)
        page = self.page
        page.get_by_placeholder("First name *").fill(first_name)
        page.get_by_placeholder("Your last name *").fill(last_name)
        page.get_by_placeholder("YYYY-MM-DD").fill(dob)
        page.get_by_placeholder("Your Street *").fill(street)
        page.get_by_placeholder("Your Postcode *").fill(postcode)
        page.get_by_placeholder("Your City *").fill(city)
        page.get_by_placeholder("Your State *").fill(state)
        page.locator("select").select_option(value=country)
        page.get_by_placeholder("Your phone *").fill(phone)
        page.get_by_placeholder("Your email *").fill(email)
        page.get_by_placeholder("Your password").fill(password)

    def submit(self) -> None:
        logger.info("[RegisterPage] Submitting registration form")
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
        self.assert_visible(self._FORM_ERROR)
