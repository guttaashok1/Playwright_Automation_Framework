"""
Page Object: Practice Software Testing — Home / Product Listing Page
URL: https://practicesoftwaretesting.com/

Locator priority: get_by_role → get_by_label → get_by_placeholder
                  → get_by_text → get_by_test_id → locator
"""
from __future__ import annotations

from loguru import logger
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class PracticeHomePage(BasePage):
    """Homepage with product grid, search, category filter, and sort."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.url = "https://practicesoftwaretesting.com"

    # ── Locators ─────────────────────────────────────────────────────────────

    def _search_input(self):
        # get_by_role (searchbox) → get_by_placeholder → get_by_test_id
        loc = self.page.get_by_role("searchbox")
        if loc.count() > 0:
            return loc.first
        loc = self.page.get_by_placeholder("Search")
        if loc.count() > 0:
            return loc.first
        return self.page.get_by_test_id("search-query")

    def _search_button(self):
        # get_by_role button → get_by_test_id
        loc = self.page.get_by_role("button", name="Search")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("search-submit")

    def _search_reset(self):
        # get_by_role → get_by_test_id
        loc = self.page.get_by_role("button", name="x")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("search-reset")

    def _product_cards(self):
        # get_by_test_id (data-test='product') — no semantic role equivalent
        return self.page.get_by_test_id("product")

    def _sort_dropdown(self):
        # get_by_label → get_by_test_id
        loc = self.page.get_by_label("Sort")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("sort")

    def _category_labels(self):
        # locator — structural checkbox labels in sidebar
        return self.page.locator(".checkbox-menu label")

    def _pagination_next(self):
        # get_by_role (link/button) → get_by_test_id
        loc = self.page.get_by_role("link", name="Next")
        if loc.count() > 0:
            return loc
        loc = self.page.get_by_role("button", name="Next")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("next-page")

    def _pagination_prev(self):
        # get_by_role → get_by_test_id
        loc = self.page.get_by_role("link", name="Previous")
        if loc.count() > 0:
            return loc
        loc = self.page.get_by_role("button", name="Previous")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("prev-page")

    def _sign_in_nav(self):
        # get_by_role (link) → get_by_test_id
        loc = self.page.get_by_role("link", name="Sign in")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("nav-sign-in")

    def _cart_nav(self):
        # get_by_test_id — cart icon nav link
        return self.page.get_by_test_id("nav-cart")

    def _cart_quantity(self):
        # locator — CSS class badge
        return self.page.locator(".cart-quantity")

    def _product_name_in_card(self):
        # get_by_test_id
        return self.page.get_by_test_id("product-name")

    def _product_price_in_card(self):
        # get_by_test_id
        return self.page.get_by_test_id("product-price")

    # ── Navigation ────────────────────────────────────────────────────────────

    def open(self) -> "PracticeHomePage":
        logger.info("[HomePage] Opening homepage")
        self.navigate_to_url(self.url)
        self.wait_for_network_idle()
        return self

    # ── Search ────────────────────────────────────────────────────────────────

    def search(self, query: str) -> "PracticeHomePage":
        logger.info(f"[HomePage] Searching for: {query}")
        inp = self._search_input()
        inp.clear()
        inp.fill(query)
        self._search_button().click()
        self.wait_for_network_idle()
        return self

    def clear_search(self) -> "PracticeHomePage":
        self._search_reset().click()
        self.wait_for_network_idle()
        return self

    def get_search_value(self) -> str:
        return self._search_input().input_value()

    # ── Products ──────────────────────────────────────────────────────────────

    def get_product_count(self) -> int:
        return self._product_cards().count()

    def get_product_names(self) -> list[str]:
        return self._product_cards().locator(
            "[data-test='product-name']"
        ).all_inner_texts()

    def get_product_prices(self) -> list[str]:
        return self._product_cards().locator(
            "[data-test='product-price']"
        ).all_inner_texts()

    def click_product_by_index(self, index: int = 0) -> None:
        logger.info(f"[HomePage] Clicking product at index {index}")
        self._product_cards().nth(index).click()
        self.wait_for_network_idle()

    def click_product_by_name(self, name: str) -> None:
        logger.info(f"[HomePage] Clicking product: {name}")
        self._product_cards().filter(has_text=name).first.click()
        self.wait_for_network_idle()

    def add_first_product_to_cart(self) -> str:
        """Click first product, return product name."""
        first_card = self._product_cards().first
        name = first_card.locator("[data-test='product-name']").inner_text()
        first_card.click()
        self.wait_for_network_idle()
        return name

    # ── Sorting ───────────────────────────────────────────────────────────────

    def sort_by(self, option: str) -> "PracticeHomePage":
        """
        Sort products. Options: 'name,asc' | 'name,desc' | 'price,asc' | 'price,desc'
        """
        logger.info(f"[HomePage] Sorting by: {option}")
        self._sort_dropdown().select_option(option)
        self.wait_for_network_idle()
        return self

    # ── Category Filter ───────────────────────────────────────────────────────

    def filter_by_category(self, category_name: str) -> "PracticeHomePage":
        logger.info(f"[HomePage] Filtering by category: {category_name}")
        self._category_labels().filter(has_text=category_name).click()
        self.wait_for_network_idle()
        return self

    def get_visible_category_names(self) -> list[str]:
        return self._category_labels().all_inner_texts()

    # ── Price Filter ──────────────────────────────────────────────────────────

    def filter_by_price(self, min_price: str, max_price: str) -> "PracticeHomePage":
        logger.info(f"[HomePage] Price filter: {min_price} – {max_price}")
        min_loc = self.page.locator("#min_price")
        max_loc = self.page.locator("#max_price")
        min_loc.clear()
        min_loc.fill(min_price)
        max_loc.clear()
        max_loc.fill(max_price)
        apply_btn = self.page.get_by_test_id("filter-apply")
        if apply_btn.is_visible():
            apply_btn.click()
            self.wait_for_network_idle()
        return self

    # ── Pagination ────────────────────────────────────────────────────────────

    def go_to_next_page(self) -> "PracticeHomePage":
        self._pagination_next().click()
        self.wait_for_network_idle()
        return self

    def go_to_prev_page(self) -> "PracticeHomePage":
        self._pagination_prev().click()
        self.wait_for_network_idle()
        return self

    def has_next_page(self) -> bool:
        loc = self._pagination_next()
        return loc.is_visible() and loc.is_enabled()

    # ── Navigation Bar ────────────────────────────────────────────────────────

    def click_sign_in(self) -> None:
        self._sign_in_nav().click()
        self.wait_for_network_idle()

    def click_cart(self) -> None:
        self._cart_nav().click()
        self.wait_for_network_idle()

    def get_cart_item_count(self) -> str:
        return self._cart_quantity().inner_text()

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_loaded(self) -> None:
        expect(self._search_input()).to_be_visible()
        expect(self._product_cards().first).to_be_visible()

    def assert_product_count_is(self, count: int) -> None:
        actual = self.get_product_count()
        assert actual == count, f"Expected {count} products, got {actual}"

    def assert_products_visible(self) -> None:
        assert self.get_product_count() > 0, "No products found on homepage"

    def assert_search_results_contain(self, text: str) -> None:
        names = self.get_product_names()
        assert any(text.lower() in n.lower() for n in names), (
            f"No product name contains '{text}'. Found: {names}"
        )

    def assert_no_products_found(self) -> None:
        """Assert the 'no results' state after a search that yields nothing."""
        assert self.get_product_count() == 0, "Expected 0 products but found some"

    def assert_sign_in_link_visible(self) -> None:
        expect(self._sign_in_nav()).to_be_visible()

    def assert_cart_quantity(self, expected: int) -> None:
        expect(self._cart_quantity()).to_contain_text(str(expected))
