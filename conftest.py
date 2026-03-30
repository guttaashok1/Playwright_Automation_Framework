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
from playwright.sync_api import Browser, BrowserContext, Page
from playwright_stealth import Stealth

try:
    from pytest_html import extras as html_extras
    _HTML_EXTRAS_AVAILABLE = True
except ImportError:
    _HTML_EXTRAS_AVAILABLE = False

from configs.config import config
from utils.api_client import APIClient
from utils.ado_client import ADOClient
from utils.confluence_client import ConfluenceClient


# ============================================================
# playwright-stealth — comprehensive anti-bot configuration
# Patches ~20 browser fingerprinting vectors that Cloudflare and
# other WAFs use to detect Playwright/headless Chrome automation.
# Applied at the BrowserContext level so it fires before every navigation.
# ============================================================

_STEALTH = Stealth(
    navigator_webdriver=True,       # navigator.webdriver → undefined
    navigator_user_agent=True,      # UA spoof
    navigator_languages=True,       # ['en-US', 'en']
    navigator_plugins=True,         # non-empty plugin list
    navigator_permissions=True,     # Notification permissions patch
    navigator_platform=True,        # Win32 platform spoof
    navigator_vendor=True,          # Google Inc. vendor
    navigator_hardware_concurrency=True,
    webgl_vendor=True,              # Intel/NVIDIA vendor string spoof
    chrome_app=True,                # window.chrome.app
    chrome_csi=True,                # window.chrome.csi
    chrome_load_times=True,         # window.chrome.loadTimes
    chrome_runtime=False,           # keep False — can break pages
    media_codecs=True,              # H264/AAC availability spoof
    hairline=True,                  # devicePixelRatio hairline fix
    iframe_content_window=True,     # iframe.contentWindow spoof
    error_prototype=True,           # stack-trace format spoof
    sec_ch_ua=True,                 # Sec-CH-UA headers spoof
)


# ============================================================
# Playwright test-id attribute configuration
# ============================================================

@pytest.fixture(scope="session", autouse=True)
def configure_test_id_attribute(playwright) -> None:
    """
    Configure Playwright to use 'data-test' as the test ID attribute.
    practicesoftwaretesting.com uses data-test (not data-testid),
    so page.get_by_test_id() must target the correct attribute.
    """
    playwright.selectors.set_test_id_attribute("data-test")


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
def browser_context_args(browser_name: str) -> dict:
    """
    Default browser context options (viewport, locale, user-agent, etc.).

    A realistic Chrome user-agent is set for Chromium so that Cloudflare
    and other WAFs do not immediately flag the request as headless-bot traffic.
    """
    # Match Playwright 1.49 bundled Chromium (version 131)
    chrome_ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
    ctx: dict = {
        "viewport": {
            "width": config.browser.VIEWPORT_WIDTH,
            "height": config.browser.VIEWPORT_HEIGHT,
        },
        "locale": "en-US",
        "timezone_id": "America/New_York",
        "record_video_dir": (
            str(config.reporting.ARTIFACTS_DIR / "videos") if not config.is_ci() else None
        ),
    }
    if browser_name == "chromium":
        ctx["user_agent"] = chrome_ua
    return ctx


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_name: str) -> dict:
    """
    Browser launch options.

    Chromium-specific flags:
    - '--disable-blink-features=AutomationControlled'  removes the JS property
      that tells pages "this is a WebDriver-controlled browser".
    - '--disable-dev-shm-usage' prevents shared-memory exhaustion in CI.

    WebKit and Firefox do not accept Chromium flags — guard every flag.
    """
    chromium_args: list[str] = []
    if browser_name == "chromium":
        # Removes navigator.webdriver = true at the Chrome level
        chromium_args.append("--disable-blink-features=AutomationControlled")
        if config.is_ci():
            chromium_args.append("--disable-dev-shm-usage")

    return {
        "headless": config.browser.HEADLESS,
        "slow_mo": config.browser.SLOW_MO,
        "args": chromium_args,
    }


@pytest.fixture(scope="function")
def page(browser: Browser, browser_context_args: dict) -> Generator[Page, None, None]:
    """
    Fresh browser page (unauthenticated) per test function.

    The stealth init-script is injected at the *context* level so that it
    executes before every navigation in this context, preventing Cloudflare
    Turnstile and similar bot-detection from blocking the tests.
    """
    context: BrowserContext = browser.new_context(**browser_context_args)
    context.set_default_timeout(config.browser.DEFAULT_TIMEOUT)
    _STEALTH.apply_stealth_sync(context)  # ← playwright-stealth: patches ~20 bot signals
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
    _STEALTH.apply_stealth_sync(context)  # ← playwright-stealth: patches ~20 bot signals
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
