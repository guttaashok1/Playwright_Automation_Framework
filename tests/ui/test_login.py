"""
UI Tests: Authentication / Login
ADO Test Plan linkage via @pytest.mark.ado marker and ado_test_case_id fixture.
"""
import pytest
from playwright.sync_api import Page

from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from configs.config import config


@pytest.mark.ui
@pytest.mark.smoke
class TestLogin:
    """Test cases covering the login functionality."""

    # ADO Test Case IDs — set these to match your ADO test case IDs
    TC_VALID_LOGIN = 1001
    TC_INVALID_PASSWORD = 1002
    TC_EMPTY_CREDENTIALS = 1003
    TC_LOGOUT = 1004

    def test_valid_login_redirects_to_dashboard(self, page: Page):
        """
        TC-1001: User with valid credentials should be redirected to dashboard.
        ADO: TC_VALID_LOGIN
        """
        login_page = LoginPage(page)
        login_page.open()
        login_page.assert_login_form_visible()

        login_page.login_and_wait(
            email=config.credentials.EMAIL,
            password=config.credentials.PASSWORD,
            expected_url_pattern="/dashboard",
        )

        dashboard = DashboardPage(page)
        dashboard.assert_loaded()
        dashboard.assert_url_is_dashboard()

    def test_invalid_password_shows_error(self, page: Page):
        """
        TC-1002: Invalid password should display an error message.
        ADO: TC_INVALID_PASSWORD
        """
        login_page = LoginPage(page)
        login_page.open()
        login_page.login(
            email=config.credentials.EMAIL,
            password="wrong_password_123!",
        )
        login_page.assert_error_displayed()

    def test_empty_credentials_shows_validation(self, page: Page):
        """
        TC-1003: Submitting empty form should show validation errors.
        ADO: TC_EMPTY_CREDENTIALS
        """
        login_page = LoginPage(page)
        login_page.open()
        login_page.click(login_page._SUBMIT_BUTTON)
        # Expect either browser validation or application-level error
        login_page.assert_url_contains("/login")

    @pytest.mark.regression
    def test_logout_redirects_to_login(self, authenticated_page: Page):
        """
        TC-1004: Logging out should redirect back to the login page.
        ADO: TC_LOGOUT
        Uses the authenticated_page fixture for pre-logged-in state.
        """
        dashboard = DashboardPage(authenticated_page)
        dashboard.assert_loaded()
        dashboard.logout()

        login_page = LoginPage(authenticated_page)
        login_page.assert_login_form_visible()

    @pytest.mark.parametrize("email,password,description", [
        ("", "password123", "empty email"),
        ("notanemail", "password123", "invalid email format"),
        ("test@example.com", "", "empty password"),
    ])
    def test_login_field_validations(self, page: Page, email: str, password: str, description: str):
        """
        Parametrized: validate various invalid input combinations.
        """
        login_page = LoginPage(page)
        login_page.open()
        login_page.fill(login_page._EMAIL_INPUT, email)
        login_page.fill(login_page._PASSWORD_INPUT, password)
        login_page.click(login_page._SUBMIT_BUTTON)
        # Should remain on login page
        login_page.assert_url_contains("/login")
