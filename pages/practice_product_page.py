"""
Page Object: Practice Software Testing — Product Detail Page
URL: https://practicesoftwaretesting.com/product/{id}

Locator priority: get_by_role → get_by_label → get_by_placeholder
                  → get_by_text → get_by_test_id → locator
"""
from __future__ import annotations

from loguru import logger
from playwright.sync_api import expect

from pages.base_page import BasePage


class PracticeProductPage(BasePage):
    """Product detail page with add-to-cart, quantity, and related products."""

    # ── Locators ─────────────────────────────────────────────────────────────

    def _product_name(self):
        # get_by_test_id — unique element, no semantic role
        return self.page.get_by_test_id("product-name")

    def _product_description(self):
        return self.page.get_by_test_id("product-description")

    def _product_price(self):
        return self.page.get_by_test_id("unit-price")

    def _product_sku(self):
        return self.page.get_by_test_id("product-sku")

    def _quantity_input(self):
        # get_by_label → get_by_test_id
        loc = self.page.get_by_label("Quantity")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("quantity")

    def _add_to_cart_button(self):
        # get_by_role (button) → get_by_test_id
        loc = self.page.get_by_role("button", name="Add to cart")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("add-to-cart")

    def _wishlist_button(self):
        # get_by_test_id
        return self.page.get_by_test_id("add-to-wishlist")

    def _compare_button(self):
        # get_by_test_id
        return self.page.get_by_test_id("add-to-compare")

    def _toast_message(self):
        # locator — CSS class, no data-test
        return self.page.locator(".toast-body")

    def _breadcrumb(self):
        # locator — structural CSS
        return self.page.locator(".breadcrumb-item")

    def _cart_quantity(self):
        # locator — CSS class badge
        return self.page.locator(".cart-quantity")

    # ── Navigation ────────────────────────────────────────────────────────────

    def open(self, product_id: str) -> "PracticeProductPage":
        url = f"https://practicesoftwaretesting.com/product/{product_id}"
        logger.info(f"[ProductPage] Opening product: {url}")
        self.navigate_to_url(url)
        self.wait_for_network_idle()
        return self

    # ── Product Info ──────────────────────────────────────────────────────────

    def get_product_name(self) -> str:
        return self._product_name().inner_text()

    def get_product_price(self) -> str:
        return self._product_price().inner_text()

    def get_product_description(self) -> str:
        return self._product_description().inner_text()

    def get_sku(self) -> str:
        return self._product_sku().inner_text()

    def get_breadcrumb_items(self) -> list[str]:
        return self._breadcrumb().all_inner_texts()

    # ── Cart Actions ──────────────────────────────────────────────────────────

    def set_quantity(self, qty: int) -> None:
        logger.info(f"[ProductPage] Setting quantity to {qty}")
        loc = self._quantity_input()
        loc.clear()
        loc.fill(str(qty))

    def get_quantity(self) -> int:
        return int(self._quantity_input().input_value())

    def add_to_cart(self) -> "PracticeProductPage":
        logger.info("[ProductPage] Adding to cart")
        self._add_to_cart_button().click()
        self.wait_for_network_idle(timeout=10_000)
        return self

    def add_to_cart_with_quantity(self, qty: int) -> "PracticeProductPage":
        self.set_quantity(qty)
        self.add_to_cart()
        return self

    def add_to_wishlist(self) -> None:
        self._wishlist_button().click()
        self.wait_for_network_idle(timeout=5_000)

    def add_to_compare(self) -> None:
        self._compare_button().click()
        self.wait_for_network_idle(timeout=5_000)

    # ── State Helpers ─────────────────────────────────────────────────────────

    def is_in_stock(self) -> bool:
        return self.page.locator(".in-stock").is_visible()

    def is_add_to_cart_enabled(self) -> bool:
        return self._add_to_cart_button().is_enabled()

    def get_toast_message(self) -> str:
        self._toast_message().wait_for(state="visible", timeout=8_000)
        return self._toast_message().inner_text()

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_loaded(self, product_name: str | None = None) -> None:
        expect(self._product_name()).to_be_visible()
        expect(self._product_price()).to_be_visible()
        expect(self._add_to_cart_button()).to_be_visible()
        if product_name:
            expect(self._product_name()).to_contain_text(product_name)

    def assert_price_format(self) -> None:
        price = self.get_product_price()
        assert price.startswith("$"), f"Price '{price}' does not start with $"

    def assert_add_to_cart_success(self) -> None:
        """Assert a success toast appeared after adding to cart."""
        expect(self._toast_message()).to_be_visible(timeout=10_000)

    def assert_cart_count_updated(self, expected_count: int) -> None:
        expect(self._cart_quantity()).to_contain_text(
            str(expected_count), timeout=8_000
        )
