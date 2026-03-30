"""
Base Page Object Model.
All page objects inherit from this class.

Key capabilities added:
  - Self-healing locators: every selector-based interaction automatically
    tries fallback strategies when the primary selector fails.
  - Visual regression: assert_visual_match() compares against baseline screenshots.
"""
from __future__ import annotations

import re
from typing import Optional

from loguru import logger
from playwright.sync_api import Page, Locator, expect

from configs.config import config
from utils.self_healing import SelfHealingLocator
from utils.visual_regression import VisualRegression


class BasePage:
    """Base class for all page objects."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.base_url = config.app.BASE_URL
        self.timeout = config.browser.DEFAULT_TIMEOUT

    # ------------------------------------------------------------------ #
    # Internal helper — returns a healed (or primary) Locator
    # ------------------------------------------------------------------ #

    def _loc(
        self,
        selector: str,
        state: str = "visible",
        timeout: Optional[int] = None,
        caller: str = "",
    ) -> Locator:
        """
        Return a working Playwright Locator.
        If self-healing is enabled, tries fallback strategies on TimeoutError.
        """
        if config.self_healing.ENABLED:
            return SelfHealingLocator(
                page=self.page,
                selector=selector,
                element_name=caller or selector,
                timeout=timeout or self.timeout,
                caller_key=f"{self.__class__.__name__}.{caller}",
            ).find(state=state)
        # Healing disabled — fall back to raw Playwright locator
        locator = self.page.locator(selector)
        locator.first.wait_for(state=state, timeout=timeout or self.timeout)
        return locator.first

    # ------------------------------------------------------------------ #
    # Navigation
    # ------------------------------------------------------------------ #

    def navigate(self, path: str = "") -> None:
        url = f"{self.base_url}/{path.lstrip('/')}" if path else self.base_url
        logger.info(f"Navigating to: {url}")
        self.page.goto(url, timeout=config.browser.NAVIGATION_TIMEOUT, wait_until="networkidle")

    def navigate_to_url(self, url: str) -> None:
        logger.info(f"Navigating to absolute URL: {url}")
        # Use "load" (not "networkidle") so the goto() doesn't time-out on
        # Cloudflare's "Just a moment…" challenge page, which keeps the
        # network busy while running its JS bot-check before redirecting.
        self.page.goto(url, timeout=config.browser.NAVIGATION_TIMEOUT, wait_until="load")
        self._bypass_cloudflare_challenge()

    def _bypass_cloudflare_challenge(self, timeout_ms: int = 20_000) -> None:
        """
        If Cloudflare's automatic JS challenge is active (title = 'Just a moment…'),
        wait up to *timeout_ms* for it to finish and redirect to the real page.
        This covers the auto-pass case; interactive Turnstile CAPTCHAs cannot be
        solved automatically and the test will fail with a clear element-not-found.
        """
        try:
            self.page.wait_for_function(
                """() => {
                    const t = (document.title || '').toLowerCase();
                    return !t.includes('just a moment') && !t.includes('checking your browser') && t !== '';
                }""",
                timeout=timeout_ms,
            )
        except Exception:
            # Challenge did not auto-clear — proceed; test assertions will fail
            # with a meaningful "element not found" message.
            logger.warning(
                f"[Cloudflare] Challenge still active after {timeout_ms}ms "
                f"on {self.page.url!r} (title={self.page.title()!r})"
            )

    def reload(self) -> None:
        self.page.reload(wait_until="networkidle")

    def go_back(self) -> None:
        self.page.go_back(wait_until="networkidle")

    # ------------------------------------------------------------------ #
    # Element interactions  (self-healing applied)
    # ------------------------------------------------------------------ #

    def get_locator(self, selector: str) -> Locator:
        """Return a raw Playwright Locator (no healing — for custom usage)."""
        return self.page.locator(selector)

    def click(self, selector: str, timeout: Optional[int] = None) -> None:
        logger.debug(f"Clicking: {selector}")
        self._loc(selector, timeout=timeout, caller="click").click(
            timeout=timeout or self.timeout
        )

    def double_click(self, selector: str) -> None:
        logger.debug(f"Double-clicking: {selector}")
        self._loc(selector, caller="double_click").dblclick(timeout=self.timeout)

    def fill(self, selector: str, value: str) -> None:
        logger.debug(f"Filling '{selector}'")
        loc = self._loc(selector, caller="fill")
        loc.clear()
        loc.fill(value)

    def type_slowly(self, selector: str, value: str, delay: int = 50) -> None:
        self._loc(selector, caller="type_slowly").press_sequentially(value, delay=delay)

    def select_option(self, selector: str, value: str) -> None:
        logger.debug(f"Selecting option '{value}' in {selector}")
        self._loc(selector, state="attached", caller="select_option").select_option(value)

    def check(self, selector: str) -> None:
        self._loc(selector, caller="check").check(timeout=self.timeout)

    def uncheck(self, selector: str) -> None:
        self._loc(selector, caller="uncheck").uncheck(timeout=self.timeout)

    def hover(self, selector: str) -> None:
        self._loc(selector, caller="hover").hover(timeout=self.timeout)

    def focus(self, selector: str) -> None:
        self._loc(selector, caller="focus").focus(timeout=self.timeout)

    def press_key(self, selector: str, key: str) -> None:
        self._loc(selector, caller="press_key").press(key)

    def upload_file(self, selector: str, file_path: str) -> None:
        self._loc(selector, state="attached", caller="upload_file").set_input_files(file_path)

    def scroll_into_view(self, selector: str) -> None:
        self._loc(selector, caller="scroll_into_view").scroll_into_view_if_needed(
            timeout=self.timeout
        )

    # ------------------------------------------------------------------ #
    # Waits
    # ------------------------------------------------------------------ #

    def wait_for_element(
        self, selector: str, state: str = "visible", timeout: Optional[int] = None
    ) -> Locator:
        return self._loc(selector, state=state, timeout=timeout, caller="wait_for_element")

    def wait_for_url(self, url_pattern: str, timeout: Optional[int] = None) -> None:
        self.page.wait_for_url(
            re.compile(url_pattern),
            timeout=timeout or config.browser.NAVIGATION_TIMEOUT,
        )

    def wait_for_network_idle(self, timeout: Optional[int] = None) -> None:
        self.page.wait_for_load_state(
            "networkidle", timeout=timeout or config.browser.NAVIGATION_TIMEOUT
        )

    def wait_for_text_in_element(
        self, selector: str, text: str, timeout: Optional[int] = None
    ) -> None:
        expect(self._loc(selector, caller="wait_for_text")).to_contain_text(
            text, timeout=timeout or self.timeout
        )

    # ------------------------------------------------------------------ #
    # Getters
    # ------------------------------------------------------------------ #

    def get_text(self, selector: str) -> str:
        return self._loc(selector, caller="get_text").inner_text()

    def get_value(self, selector: str) -> str:
        return self._loc(selector, caller="get_value").input_value()

    def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        return self._loc(selector, caller="get_attribute").get_attribute(attribute)

    def get_all_texts(self, selector: str) -> list[str]:
        return self.page.locator(selector).all_inner_texts()

    def get_current_url(self) -> str:
        return self.page.url

    def get_title(self) -> str:
        return self.page.title()

    # ------------------------------------------------------------------ #
    # Assertions
    # ------------------------------------------------------------------ #

    def assert_visible(self, selector: str, timeout: Optional[int] = None) -> None:
        expect(self._loc(selector, caller="assert_visible")).to_be_visible(
            timeout=timeout or self.timeout
        )

    def assert_hidden(self, selector: str, timeout: Optional[int] = None) -> None:
        expect(self.page.locator(selector)).to_be_hidden(timeout=timeout or self.timeout)

    def assert_enabled(self, selector: str) -> None:
        expect(self._loc(selector, caller="assert_enabled")).to_be_enabled(
            timeout=self.timeout
        )

    def assert_disabled(self, selector: str) -> None:
        expect(self.page.locator(selector)).to_be_disabled(timeout=self.timeout)

    def assert_text(self, selector: str, text: str, exact: bool = False) -> None:
        loc = self._loc(selector, caller="assert_text")
        if exact:
            expect(loc).to_have_text(text, timeout=self.timeout)
        else:
            expect(loc).to_contain_text(text, timeout=self.timeout)

    def assert_url_contains(self, partial_url: str) -> None:
        expect(self.page).to_have_url(re.compile(partial_url))

    def assert_title(self, title: str) -> None:
        expect(self.page).to_have_title(title)

    def assert_checked(self, selector: str) -> None:
        expect(self._loc(selector, caller="assert_checked")).to_be_checked(
            timeout=self.timeout
        )

    # ------------------------------------------------------------------ #
    # Visual regression
    # ------------------------------------------------------------------ #

    def assert_visual_match(
        self,
        name: str,
        threshold: float | None = None,
        mask_selectors: list[str] | None = None,
        update_baseline: bool = False,
    ) -> None:
        """
        Assert the current page screenshot matches the stored baseline.

        Args:
            name             : Unique baseline name (e.g. "login_page_default").
            threshold        : Max allowed pixel-diff ratio (default: config.visual.THRESHOLD).
            mask_selectors   : CSS selectors of dynamic regions to ignore in diff.
            update_baseline  : Force-overwrite the stored baseline.

        On first run → creates baseline, test passes.
        On subsequent runs → fails if diff exceeds threshold, saves diff image.
        """
        if not config.visual.ENABLED:
            logger.debug(f"[Visual] Skipping assert_visual_match('{name}') — disabled.")
            return

        vr = VisualRegression(
            threshold=threshold or config.visual.THRESHOLD,
            baseline_dir=config.visual.BASELINE_DIR,
            diff_dir=config.visual.DIFF_DIR,
        )
        passed = vr.compare(
            self.page, name,
            mask_selectors=mask_selectors or [],
            update_baseline=update_baseline,
        )
        assert passed, (
            f"Visual regression failed for '{name}'. "
            f"Diff image: {config.visual.DIFF_DIR / (name + '_diff.png')}"
        )

    # ------------------------------------------------------------------ #
    # State checks
    # ------------------------------------------------------------------ #

    def is_visible(self, selector: str) -> bool:
        return self.page.locator(selector).is_visible()

    def is_enabled(self, selector: str) -> bool:
        return self.page.locator(selector).is_enabled()

    def is_checked(self, selector: str) -> bool:
        return self.page.locator(selector).is_checked()

    def element_count(self, selector: str) -> int:
        return self.page.locator(selector).count()

    # ------------------------------------------------------------------ #
    # Screenshots & Debugging
    # ------------------------------------------------------------------ #

    def take_screenshot(self, name: str = "screenshot") -> bytes:
        path = config.reporting.ARTIFACTS_DIR / f"{name}.png"
        config.reporting.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Taking screenshot: {path}")
        return self.page.screenshot(path=str(path), full_page=True)

    def highlight_element(self, selector: str) -> None:
        self.page.evaluate(
            f"document.querySelector('{selector}').style.border = '3px solid red'"
        )

    # ------------------------------------------------------------------ #
    # JavaScript execution
    # ------------------------------------------------------------------ #

    def execute_script(self, script: str, *args):
        return self.page.evaluate(script, *args)

    def scroll_to_bottom(self) -> None:
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    def scroll_to_top(self) -> None:
        self.page.evaluate("window.scrollTo(0, 0)")
