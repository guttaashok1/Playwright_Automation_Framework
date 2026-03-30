"""
Page Object: Practice Software Testing — Home / Product Listing Page
URL: https://practicesoftwaretesting.com/
"""
from __future__ import annotations

from loguru import logger
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class PracticeHomePage(BasePage):
    """Homepage with product grid, search, category filter, and sort."""

    # ── Selectors ────────────────────────────────────────────────────────────
    _NAVBAR_BRAND        = "a.navbar-brand"
    _SEARCH_INPUT        = "[data-test='search-query']"
    _SEARCH_BUTTON       = "[data-test='search-submit']"
    _SEARCH_RESET        = "[data-test='search-reset']"
    _PRODUCT_CARDS       = "[data-test='product']"
    _PRODUCT_NAME        = "[data-test='product-name']"
    _PRODUCT_PRICE       = "[data-test='product-price']"
    _SORT_DROPDOWN       = "[data-test='sort']"
    _CATEGORY_LABELS     = ".checkbox-menu label"
    _CATEGORY_FILTER     = "label.checkbox-menu"
    _FILTER_CHECKBOX     = "input[type='checkbox']"
    _PAGINATION_NEXT     = "[data-test='next-page']"
    _PAGINATION_PREV     = "[data-test='prev-page']"
    _SIGN_IN_NAV         = "[data-test='nav-sign-in']"
    _CART_NAV            = "[data-test='nav-cart']"
    _CART_QUANTITY       = ".cart-quantity"
    _FILTERS_SIDEBAR     = ".filters-sidebar"
    _PRICE_MIN           = "#min_price"
    _PRICE_MAX           = "#max_price"
    _FILTER_APPLY_BTN    = "[data-test='filter-apply']"
    _PRODUCT_SALE_BADGE  = ".sale-badge"
    _TOAST_MESSAGE       = ".toast-body"
    _PAGE_HEADER         = "h3"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.url = "https://practicesoftwaretesting.com"

    # ── Navigation ────────────────────────────────────────────────────────────

    def open(self) -> "PracticeHomePage":
        logger.info("[HomePage] Opening homepage")
        self.navigate_to_url(self.url)
        self.wait_for_network_idle()
        return self

    # ── Search ────────────────────────────────────────────────────────────────

    def search(self, query: str) -> "PracticeHomePage":
        logger.info(f"[HomePage] Searching for: {query}")
        self.fill(self._SEARCH_INPUT, query)
        self.click(self._SEARCH_BUTTON)
        self.wait_for_network_idle()
        return self

    def clear_search(self) -> "PracticeHomePage":
        self.click(self._SEARCH_RESET)
        self.wait_for_network_idle()
        return self

    def get_search_value(self) -> str:
        return self.get_value(self._SEARCH_INPUT)

    # ── Products ──────────────────────────────────────────────────────────────

    def get_product_count(self) -> int:
        return self.element_count(self._PRODUCT_CARDS)

    def get_product_names(self) -> list[str]:
        return self.page.locator(f"{self._PRODUCT_CARDS} {self._PRODUCT_NAME}").all_inner_texts()

    def get_product_prices(self) -> list[str]:
        return self.page.locator(f"{self._PRODUCT_CARDS} {self._PRODUCT_PRICE}").all_inner_texts()

    def click_product_by_index(self, index: int = 0) -> None:
        logger.info(f"[HomePage] Clicking product at index {index}")
        self.page.locator(self._PRODUCT_CARDS).nth(index).click()
        self.wait_for_network_idle()

    def click_product_by_name(self, name: str) -> None:
        logger.info(f"[HomePage] Clicking product: {name}")
        self.page.locator(self._PRODUCT_CARDS).filter(has_text=name).first.click()
        self.wait_for_network_idle()

    def add_first_product_to_cart(self) -> str:
        """Click first product, add to cart, return product name."""
        first_product = self.page.locator(self._PRODUCT_CARDS).first
        name = first_product.locator(self._PRODUCT_NAME).inner_text()
        first_product.click()
        self.wait_for_network_idle()
        return name

    # ── Sorting ───────────────────────────────────────────────────────────────

    def sort_by(self, option: str) -> "PracticeHomePage":
        """
        Sort products. Options: 'name,asc' | 'name,desc' | 'price,asc' | 'price,desc'
        """
        logger.info(f"[HomePage] Sorting by: {option}")
        self.select_option(self._SORT_DROPDOWN, option)
        self.wait_for_network_idle()
        return self

    # ── Category Filter ───────────────────────────────────────────────────────

    def filter_by_category(self, category_name: str) -> "PracticeHomePage":
        logger.info(f"[HomePage] Filtering by category: {category_name}")
        self.page.locator(self._CATEGORY_LABELS).filter(has_text=category_name).click()
        self.wait_for_network_idle()
        return self

    def get_visible_category_names(self) -> list[str]:
        return self.page.locator(self._CATEGORY_LABELS).all_inner_texts()

    # ── Price Filter ──────────────────────────────────────────────────────────

    def filter_by_price(self, min_price: str, max_price: str) -> "PracticeHomePage":
        logger.info(f"[HomePage] Price filter: {min_price} – {max_price}")
        self.fill(self._PRICE_MIN, min_price)
        self.fill(self._PRICE_MAX, max_price)
        if self.is_visible(self._FILTER_APPLY_BTN):
            self.click(self._FILTER_APPLY_BTN)
            self.wait_for_network_idle()
        return self

    # ── Pagination ────────────────────────────────────────────────────────────

    def go_to_next_page(self) -> "PracticeHomePage":
        self.click(self._PAGINATION_NEXT)
        self.wait_for_network_idle()
        return self

    def go_to_prev_page(self) -> "PracticeHomePage":
        self.click(self._PAGINATION_PREV)
        self.wait_for_network_idle()
        return self

    def has_next_page(self) -> bool:
        return self.is_visible(self._PAGINATION_NEXT) and self.is_enabled(self._PAGINATION_NEXT)

    # ── Navigation Bar ────────────────────────────────────────────────────────

    def click_sign_in(self) -> None:
        self.click(self._SIGN_IN_NAV)
        self.wait_for_network_idle()

    def click_cart(self) -> None:
        self.click(self._CART_NAV)
        self.wait_for_network_idle()

    def get_cart_item_count(self) -> str:
        return self.get_text(self._CART_QUANTITY)

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_loaded(self) -> None:
        self.assert_visible(self._SEARCH_INPUT)
        self.assert_visible(self._PRODUCT_CARDS)

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
        self.assert_visible(self._SIGN_IN_NAV)

    def assert_cart_quantity(self, expected: int) -> None:
        expect(self.page.locator(self._CART_QUANTITY)).to_contain_text(str(expected))
