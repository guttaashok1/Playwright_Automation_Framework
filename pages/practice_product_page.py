"""
Page Object: Practice Software Testing — Product Detail Page
URL: https://practicesoftwaretesting.com/product/{id}
"""
from __future__ import annotations

from loguru import logger
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class PracticeProductPage(BasePage):
    """Product detail page with add-to-cart, quantity, and related products."""

    # ── Selectors ────────────────────────────────────────────────────────────
    _PRODUCT_NAME        = "[data-test='product-name']"
    _PRODUCT_DESCRIPTION = "[data-test='product-description']"
    _PRODUCT_PRICE       = "[data-test='unit-price']"
    _PRODUCT_SKU         = "[data-test='product-sku']"
    _QUANTITY_INPUT      = "[data-test='quantity']"
    _ADD_TO_CART_BUTTON  = "[data-test='add-to-cart']"
    _WISHLIST_BUTTON     = "[data-test='add-to-wishlist']"
    _COMPARE_BUTTON      = "[data-test='add-to-compare']"
    _PRODUCT_IMAGE       = "img.product-img"
    _STOCK_STATUS        = ".in-stock, .out-of-stock"
    _TOAST_MESSAGE       = ".toast-body"
    _BREADCRUMB          = ".breadcrumb-item"
    _RELATED_PRODUCTS    = ".related-products [data-test='product']"
    _PRODUCT_CATEGORY    = "[data-test='product-category']"
    _PRODUCT_BRAND       = "[data-test='product-brand']"
    _CART_NAV            = "[data-test='nav-cart']"
    _CART_QUANTITY       = ".cart-quantity"

    # ── Navigation ────────────────────────────────────────────────────────────

    def open(self, product_id: str) -> "PracticeProductPage":
        url = f"https://practicesoftwaretesting.com/product/{product_id}"
        logger.info(f"[ProductPage] Opening product: {url}")
        self.navigate_to_url(url)
        self.wait_for_network_idle()
        return self

    # ── Product Info ──────────────────────────────────────────────────────────

    def get_product_name(self) -> str:
        return self.get_text(self._PRODUCT_NAME)

    def get_product_price(self) -> str:
        return self.get_text(self._PRODUCT_PRICE)

    def get_product_description(self) -> str:
        return self.get_text(self._PRODUCT_DESCRIPTION)

    def get_sku(self) -> str:
        return self.get_text(self._PRODUCT_SKU)

    def get_breadcrumb_items(self) -> list[str]:
        return self.page.locator(self._BREADCRUMB).all_inner_texts()

    # ── Cart Actions ──────────────────────────────────────────────────────────

    def set_quantity(self, qty: int) -> None:
        logger.info(f"[ProductPage] Setting quantity to {qty}")
        loc = self.page.locator(self._QUANTITY_INPUT)
        loc.clear()
        loc.fill(str(qty))

    def get_quantity(self) -> int:
        return int(self.get_value(self._QUANTITY_INPUT))

    def add_to_cart(self) -> "PracticeProductPage":
        logger.info("[ProductPage] Adding to cart")
        self.click(self._ADD_TO_CART_BUTTON)
        self.wait_for_network_idle(timeout=10_000)
        return self

    def add_to_cart_with_quantity(self, qty: int) -> "PracticeProductPage":
        self.set_quantity(qty)
        self.add_to_cart()
        return self

    def add_to_wishlist(self) -> None:
        self.click(self._WISHLIST_BUTTON)
        self.wait_for_network_idle(timeout=5_000)

    def add_to_compare(self) -> None:
        self.click(self._COMPARE_BUTTON)
        self.wait_for_network_idle(timeout=5_000)

    # ── State Helpers ─────────────────────────────────────────────────────────

    def is_in_stock(self) -> bool:
        return self.is_visible(".in-stock")

    def is_add_to_cart_enabled(self) -> bool:
        return self.is_enabled(self._ADD_TO_CART_BUTTON)

    def get_toast_message(self) -> str:
        self.wait_for_element(self._TOAST_MESSAGE, timeout=8_000)
        return self.get_text(self._TOAST_MESSAGE)

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_loaded(self, product_name: str | None = None) -> None:
        self.assert_visible(self._PRODUCT_NAME)
        self.assert_visible(self._PRODUCT_PRICE)
        self.assert_visible(self._ADD_TO_CART_BUTTON)
        if product_name:
            self.assert_text(self._PRODUCT_NAME, product_name)

    def assert_price_format(self) -> None:
        price = self.get_product_price()
        assert price.startswith("$"), f"Price '{price}' does not start with $"

    def assert_add_to_cart_success(self) -> None:
        """Assert a success toast appeared after adding to cart."""
        expect(self.page.locator(self._TOAST_MESSAGE)).to_be_visible(timeout=10_000)

    def assert_cart_count_updated(self, expected_count: int) -> None:
        expect(self.page.locator(self._CART_QUANTITY)).to_contain_text(
            str(expected_count), timeout=8_000
        )
