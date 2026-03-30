"""
UI Tests: Practice Software Testing — Authentication (Login & Register)
Covers: valid login, invalid credentials, field validation, logout, registration.
"""
import pytest
from playwright.sync_api import Page

from pages.practice_auth_page import PracticeLoginPage, PracticeRegisterPage
from pages.practice_home_page import PracticeHomePage
from test_data.practice_test_data import (
    CUSTOMER_EMAIL,
    CUSTOMER_PASSWORD,
    make_user,
)


@pytest.mark.ui
@pytest.mark.smoke
class TestPracticeLogin:
    """Smoke tests for login flow."""

    def test_valid_login_redirects_to_account(self, page: Page):
        """Valid credentials log the user in and redirect to /account."""
        login = PracticeLoginPage(page)
        login.open()
        login.assert_login_form_visible()
        login.login(CUSTOMER_EMAIL, CUSTOMER_PASSWORD)
        login.assert_logged_in()

    def test_login_page_shows_form(self, page: Page):
        """Login page renders email, password, and submit button."""
        login = PracticeLoginPage(page)
        login.open()
        login.assert_login_form_visible()

    def test_register_link_visible_on_login_page(self, page: Page):
        """'Register your account' link is visible from the login page."""
        from playwright.sync_api import expect
        login = PracticeLoginPage(page)
        login.open()
        expect(login._register_link()).to_be_visible()


@pytest.mark.ui
@pytest.mark.regression
class TestPracticeLoginValidation:
    """Negative tests and field validation for the login form."""

    def test_invalid_password_shows_error(self, page: Page):
        """Wrong password displays an error message."""
        login = PracticeLoginPage(page)
        login.open()
        login.login(CUSTOMER_EMAIL, "wrong_password_!@#")
        login.assert_still_on_login()
        login.assert_error_visible()

    def test_invalid_email_shows_error(self, page: Page):
        """Non-existent email displays an error message."""
        login = PracticeLoginPage(page)
        login.open()
        login.login("nobody@nowhere.invalid", "password123")
        login.assert_still_on_login()
        login.assert_error_visible()

    def test_empty_form_submission(self, page: Page):
        """Submitting an empty login form stays on the login page."""
        login = PracticeLoginPage(page)
        login.open()
        login.click_login()
        login.assert_still_on_login()

    def test_empty_password_shows_error(self, page: Page):
        """Submitting without a password stays on login."""
        login = PracticeLoginPage(page)
        login.open()
        login.enter_email(CUSTOMER_EMAIL)
        login.click_login()
        login.assert_still_on_login()

    @pytest.mark.parametrize("email,password,label", [
        ("",                       "welcome01",      "empty email"),
        (CUSTOMER_EMAIL,           "",               "empty password"),
        ("notanemail",             "welcome01",      "invalid email format"),
        ("test@example.com",       "wrongpass",      "wrong password"),
    ])
    def test_login_field_combinations(self, page: Page, email: str, password: str, label: str):
        """Parametrized: various invalid credential combinations stay on login."""
        login = PracticeLoginPage(page)
        login.open()
        login.enter_email(email)
        login.enter_password(password)
        login.click_login()
        login.assert_still_on_login()


@pytest.mark.ui
@pytest.mark.regression
class TestPracticeLogout:
    """Tests for logout functionality."""

    def test_logout_redirects_to_home_or_login(self, page: Page):
        """Logging out returns the user to home or login page."""
        login = PracticeLoginPage(page)
        login.open()
        login.login(CUSTOMER_EMAIL, CUSTOMER_PASSWORD)
        login.assert_logged_in()
        login.logout()
        # After logout, should be on home or login
        url = page.url
        assert "practicesoftwaretesting.com" in url
        assert "/account" not in url, f"Still on account page after logout: {url}"

    def test_sign_in_link_visible_after_logout(self, page: Page):
        """After logout, the Sign In nav link reappears."""
        login = PracticeLoginPage(page)
        login.open()
        login.login(CUSTOMER_EMAIL, CUSTOMER_PASSWORD)
        login.logout()
        home = PracticeHomePage(page)
        home.assert_sign_in_link_visible()


@pytest.mark.ui
@pytest.mark.regression
class TestPracticeRegister:
    """Tests for the user registration flow."""

    def test_register_page_loads(self, page: Page):
        """Registration page opens and form is visible."""
        register = PracticeRegisterPage(page)
        register.open()
        register.assert_form_visible()

    def test_register_new_user(self, page: Page):
        """
        End-to-end: register a new user and verify redirect to login.
        Uses dynamically generated test data to avoid conflicts.
        """
        user = make_user()
        register = PracticeRegisterPage(page)
        register.open()
        register.register(
            first_name=user["first_name"],
            last_name=user["last_name"],
            email=user["email"],
            password=user["password"],
            dob=user["dob"],
            street=user["street"],
            postcode=user["postcode"],
            city=user["city"],
            state=user["state"],
            country=user["country"],
            phone=user["phone"],
        )
        register.assert_registration_success()

    def test_register_then_login(self, page: Page):
        """Register a new user and immediately log in with those credentials."""
        user = make_user()

        # Register
        register = PracticeRegisterPage(page)
        register.open()
        register.register(
            first_name=user["first_name"],
            last_name=user["last_name"],
            email=user["email"],
            password=user["password"],
        )
        register.assert_registration_success()

        # Login with new account
        login = PracticeLoginPage(page)
        login.login(user["email"], user["password"])
        login.assert_logged_in()

    def test_register_link_on_login_page_navigates(self, page: Page):
        """'Register your account' link on login page goes to /auth/register."""
        login = PracticeLoginPage(page)
        login.open()
        login.click_register_link()
        register = PracticeRegisterPage(page)
        register.assert_form_visible()
