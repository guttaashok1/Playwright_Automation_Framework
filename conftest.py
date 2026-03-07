"""
Root conftest.py — Pytest fixtures shared across all tests.

Fixture hierarchy:
  session scope:  api_client, ado_client, confluence_client
  function scope: page, authenticated_page, authenticated_api_client
"""
from __future__ import annotations

import base64
import os
from typing import Generator

import pytest
from loguru import logger
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

try:
    from pytest_html import extras as html_extras
    _HTML_EXTRAS_AVAILABLE = True
except ImportError:
    _HTML_EXTRAS_AVAILABLE = False

from configs.config import config
from utils.api_client import APIClient
from utils.ado_client import ADOClient, TestOutcome
from utils.confluence_client import ConfluenceClient


# ============================================================
# Custom CLI options
# ============================================================

def pytest_addoption(parser):
    """Register custom CLI flags."""
    parser.addoption(
        "--update-baselines",
        action="store_true",
        default=False,
        help="Force-overwrite all visual regression baselines.",
    )


@pytest.fixture(scope="session")
def update_baselines(request) -> bool:
    """Expose --update-baselines flag to tests / page objects."""
    return request.config.getoption("--update-baselines")


# ============================================================
# Playwright browser fixtures
# ============================================================

@pytest.fixture(scope="session")
def browser_context_args() -> dict:
    """Default browser context options (viewport, locale, etc.)."""
    return {
        "viewport": {
            "width": config.browser.VIEWPORT_WIDTH,
            "height": config.browser.VIEWPORT_HEIGHT,
        },
        "locale": "en-US",
        "timezone_id": "America/New_York",
        "record_video_dir": str(config.reporting.ARTIFACTS_DIR / "videos") if not config.is_ci() else None,
    }


@pytest.fixture(scope="session")
def browser_type_launch_args() -> dict:
    """Browser launch options."""
    return {
        "headless": config.browser.HEADLESS,
        "slow_mo": config.browser.SLOW_MO,
        "args": ["--disable-dev-shm-usage"] if config.is_ci() else [],
    }


@pytest.fixture(scope="function")
def page(browser: Browser, browser_context_args: dict) -> Generator[Page, None, None]:
    """Fresh browser page (unauthenticated) per test function."""
    context: BrowserContext = browser.new_context(**browser_context_args)
    context.set_default_timeout(config.browser.DEFAULT_TIMEOUT)
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="function")
def authenticated_page(browser: Browser, browser_context_args: dict) -> Generator[Page, None, None]:
    """
    Browser page pre-authenticated via UI login.
    Uses session storage to avoid re-login for each test.
    """
    context: BrowserContext = browser.new_context(**browser_context_args)
    context.set_default_timeout(config.browser.DEFAULT_TIMEOUT)
    page = context.new_page()

    # Navigate to login and authenticate
    page.goto(f"{config.app.BASE_URL}/login", wait_until="networkidle")
    page.fill("input[type='email']", config.credentials.EMAIL)
    page.fill("input[type='password']", config.credentials.PASSWORD)
    page.click("button[type='submit']")
    page.wait_for_url("**/dashboard**", timeout=config.browser.NAVIGATION_TIMEOUT)
    logger.info(f"[Fixture] authenticated_page — logged in as {config.credentials.EMAIL}")

    yield page
    context.close()


# ============================================================
# API fixtures
# ============================================================

@pytest.fixture(scope="session")
def api_client() -> Generator[APIClient, None, None]:
    """Unauthenticated API client (session-scoped)."""
    client = APIClient()
    yield client
    client.close()


@pytest.fixture(scope="function")
def authenticated_api_client() -> Generator[APIClient, None, None]:
    """API client with a fresh auth token per test function."""
    client = APIClient()
    if config.credentials.EMAIL and config.credentials.PASSWORD:
        try:
            client.login(config.credentials.EMAIL, config.credentials.PASSWORD)
        except Exception as e:
            logger.warning(f"[Fixture] Could not authenticate API client: {e}")
    yield client
    client.close()


# ============================================================
# ADO fixtures
# ============================================================

@pytest.fixture(scope="session")
def ado_client() -> ADOClient:
    """ADO client (session-scoped)."""
    return ADOClient()


@pytest.fixture(scope="session")
def ado_test_run_id(ado_client: ADOClient) -> int:
    """
    Create a single ADO test run for the entire test session.
    Results are pushed to this run via the ado_result fixture.
    """
    ci_build = os.getenv("GITHUB_RUN_NUMBER", "local")
    run_id = ado_client.create_test_run(
        name=f"Automated Run — {config.app.ENVIRONMENT} — Build #{ci_build}"
    )
    yield run_id
    ado_client.complete_test_run(run_id)


# ============================================================
# Confluence fixtures
# ============================================================

@pytest.fixture(scope="session")
def confluence_client() -> ConfluenceClient:
    """Confluence client (session-scoped)."""
    return ConfluenceClient()


# ============================================================
# Reporting hooks
# ============================================================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    After each test:
    - Attach screenshot on failure (for UI tests with a 'page' fixture)
    - Log outcome
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        page: Page | None = item.funcargs.get("page") or item.funcargs.get("authenticated_page")
        if page:
            config.reporting.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
            status_label = "PASSED" if report.passed else "FAILED"
            screenshot_path = config.reporting.ARTIFACTS_DIR / f"{status_label}_{item.name}.png"
            try:
                screenshot_bytes = page.screenshot(path=str(screenshot_path), full_page=True)

                # Embed screenshot directly into the pytest-html report
                if _HTML_EXTRAS_AVAILABLE:
                    b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                    report.extras = getattr(report, "extras", [])
                    report.extras.append(
                        html_extras.image(b64, name=f"Screenshot — {status_label}")
                    )

                if report.failed:
                    logger.error(f"[Screenshot] {screenshot_path}")
                else:
                    logger.debug(f"[Screenshot] {screenshot_path}")
            except Exception as e:
                logger.warning(f"Could not capture screenshot: {e}")


def pytest_sessionstart(session):
    """Create required output directories before the session starts."""
    config.reporting.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    config.reporting.ALLURE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    config.reporting.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"[Session] Environment: {config.get_env()}")
    logger.info(f"[Session] Base URL: {config.app.BASE_URL}")


def pytest_sessionfinish(session, exitstatus):
    """Called after the entire test session finishes."""
    logger.info(f"[Session] Finished with exit status: {exitstatus}")
