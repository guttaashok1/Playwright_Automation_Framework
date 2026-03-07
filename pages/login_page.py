"""
Login Page Object.
Example page object demonstrating the POM pattern.
Replace selectors to match your application.
"""
from __future__ import annotations

from loguru import logger
from playwright.sync_api import Page

from pages.base_page import BasePage


class LoginPage(BasePage):
    """Page object for the login/authentication page."""

    # Selectors - update these to match your application
    _URL_PATH = "/login"
    _EMAIL_INPUT = "[data-testid='email-input'], input[name='email'], input[type='email']"
    _PASSWORD_INPUT = "[data-testid='password-input'], input[name='password'], input[type='password']"
    _SUBMIT_BUTTON = "[data-testid='login-button'], button[type='submit']"
    _ERROR_MESSAGE = "[data-testid='error-message'], .error-message, [role='alert']"
    _FORGOT_PASSWORD_LINK = "a[href*='forgot'], [data-testid='forgot-password']"
    _REMEMBER_ME_CHECKBOX = "input[name='rememberMe'], [data-testid='remember-me']"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def open(self) -> "LoginPage":
        """Navigate to the login page."""
        self.navigate(self._URL_PATH)
        return self

    def login(self, email: str, password: str) -> None:
        """Perform login with given credentials."""
        logger.info(f"Logging in as: {email}")
        self.fill(self._EMAIL_INPUT, email)
        self.fill(self._PASSWORD_INPUT, password)
        self.click(self._SUBMIT_BUTTON)

    def login_and_wait(self, email: str, password: str, expected_url_pattern: str = "/dashboard") -> None:
        """Login and wait for redirect to expected page."""
        self.login(email, password)
        self.wait_for_url(expected_url_pattern)

    def get_error_message(self) -> str:
        """Return the displayed error message text."""
        self.wait_for_element(self._ERROR_MESSAGE)
        return self.get_text(self._ERROR_MESSAGE)

    def check_remember_me(self) -> "LoginPage":
        self.check(self._REMEMBER_ME_CHECKBOX)
        return self

    def click_forgot_password(self) -> None:
        self.click(self._FORGOT_PASSWORD_LINK)

    def assert_error_displayed(self, expected_message: str = "") -> None:
        self.assert_visible(self._ERROR_MESSAGE)
        if expected_message:
            self.assert_text(self._ERROR_MESSAGE, expected_message)

    def assert_login_form_visible(self) -> None:
        self.assert_visible(self._EMAIL_INPUT)
        self.assert_visible(self._PASSWORD_INPUT)
        self.assert_visible(self._SUBMIT_BUTTON)
