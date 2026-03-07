"""
Dashboard Page Object.
Example page object for a post-login dashboard page.
"""
from __future__ import annotations

from playwright.sync_api import Page

from pages.base_page import BasePage


class DashboardPage(BasePage):
    """Page object for the main dashboard."""

    _URL_PATH = "/dashboard"
    _PAGE_HEADING = "h1, [data-testid='page-heading']"
    _NAV_MENU = "nav, [data-testid='sidebar-nav']"
    _USER_MENU = "[data-testid='user-menu'], .user-avatar"
    _LOGOUT_BUTTON = "[data-testid='logout-button'], a[href*='logout']"
    _NOTIFICATION_BADGE = "[data-testid='notification-count'], .notification-badge"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def open(self) -> "DashboardPage":
        self.navigate(self._URL_PATH)
        return self

    def logout(self) -> None:
        self.click(self._USER_MENU)
        self.click(self._LOGOUT_BUTTON)
        self.wait_for_url("/login")

    def get_heading(self) -> str:
        return self.get_text(self._PAGE_HEADING)

    def get_notification_count(self) -> int:
        if not self.is_visible(self._NOTIFICATION_BADGE):
            return 0
        text = self.get_text(self._NOTIFICATION_BADGE)
        return int(text) if text.isdigit() else 0

    def assert_loaded(self) -> None:
        self.assert_visible(self._PAGE_HEADING)
        self.assert_visible(self._NAV_MENU)

    def assert_url_is_dashboard(self) -> None:
        self.assert_url_contains("/dashboard")
