"""
UI Tests: Dashboard
Demonstrates use of authenticated_page fixture and screenshot on failure.

NOTE: Template file for a generic dashboard app.
      Skipped globally — not applicable to practicesoftwaretesting.com.
"""
import pytest
from playwright.sync_api import Page

from pages.dashboard_page import DashboardPage

pytestmark = pytest.mark.skip(reason="Template test — targets generic /dashboard app, not practicesoftwaretesting.com")


@pytest.mark.ui
@pytest.mark.regression
class TestDashboard:
    """Test cases covering the main dashboard."""

    def test_dashboard_loads_successfully(self, authenticated_page: Page):
        """Dashboard should display heading and navigation after login."""
        dashboard = DashboardPage(authenticated_page)
        dashboard.assert_loaded()

    def test_dashboard_url_is_correct(self, authenticated_page: Page):
        """URL should contain /dashboard after successful authentication."""
        dashboard = DashboardPage(authenticated_page)
        dashboard.assert_url_is_dashboard()

    def test_page_title_is_set(self, authenticated_page: Page):
        """Browser tab title should be set."""
        dashboard = DashboardPage(authenticated_page)
        title = dashboard.get_title()
        assert title, "Page title should not be empty"
