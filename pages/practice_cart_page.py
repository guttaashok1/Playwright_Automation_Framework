"""
Page Object: Practice Software Testing — Shopping Cart Page
URL: https://practicesoftwaretesting.com/checkout

Locator priority: get_by_role → get_by_label → get_by_placeholder
                  → get_by_text → get_by_test_id → locator
"""
from __future__ import annotations

from loguru import logger
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class PracticeCartPage(BasePage):
    """Shopping cart page — view, update quantity, remove items, proceed."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.url = "https://practicesoftwaretesting.com/checkout"

    # ── Locators ─────────────────────────────────────────────────────────────

    def _cart_items(self):
        # get_by_test_id — each cart row
        return self.page.get_by_test_id("cart-item")

    def _item_title(self):
        return self.page.get_by_test_id("product-title")

    def _item_price(self):
        return self.page.get_by_test_id("product-price")

    def _item_qty_input(self):
        return self.page.get_by_test_id("product-quantity")

    def _item_remove_btn(self):
        # get_by_role → get_by_test_id
        loc = self.page.get_by_role("button", name="Delete")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("delete-product")

    def _cart_total(self):
        return self.page.get_by_test_id("cart-total")

    def _proceed_to_checkout_btn(self):
        # get_by_role (button) → get_by_test_id
        loc = self.page.get_by_role("button", name="Proceed to checkout")
        if loc.count() > 0:
            return loc
        loc = self.page.get_by_role("link", name="Proceed to checkout")
        if loc.count() > 0:
            return loc
        return self.page.get_by_test_id("proceed-1")

    def _empty_cart_message(self):
        # get_by_text → get_by_test_id
        loc = self.page.get_by_test_id("empty-cart")
        if loc.count() > 0:
            return loc
        return self.page.get_by_text("Your cart is empty")

    def _nav_cart(self):
        return self.page.get_by_test_id("nav-cart")

    # ── Navigation ────────────────────────────────────────────────────────────

    def open(self) -> "PracticeCartPage":
        logger.info("[CartPage] Opening cart")
        self.navigate_to_url(self.url)
        self.wait_for_network_idle()
        return self

    def open_via_navbar(self) -> "PracticeCartPage":
        self._nav_cart().click()
        self.wait_for_network_idle()
        return self

    # ── Cart Contents ─────────────────────────────────────────────────────────

    def get_item_count(self) -> int:
        return self._cart_items().count()

    def get_item_names(self) -> list[str]:
        return self._cart_items().locator(
            "[data-test='product-title']"
        ).all_inner_texts()

    def get_item_prices(self) -> list[str]:
        return self._cart_items().locator(
            "[data-test='product-price']"
        ).all_inner_texts()

    def get_item_quantities(self) -> list[int]:
        items = self._cart_items().locator(
            "[data-test='product-quantity']"
        ).all()
        return [int(item.input_value()) for item in items]

    def get_cart_total(self) -> str:
        return self._cart_total().inner_text()

    def is_empty(self) -> bool:
        loc = self.page.get_by_test_id("empty-cart")
        if loc.count() > 0:
            return loc.is_visible()
        return self.page.get_by_text("Your cart is empty").is_visible()

    # ── Item Operations ───────────────────────────────────────────────────────

    def update_item_quantity(self, index: int, qty: int) -> None:
        logger.info(f"[CartPage] Updating item {index} quantity to {qty}")
        qty_loc = self._cart_items().locator(
            "[data-test='product-quantity']"
        ).nth(index)
        qty_loc.clear()
        qty_loc.fill(str(qty))
        qty_loc.press("Tab")
        self.wait_for_network_idle(timeout=5_000)

    def remove_item(self, index: int = 0) -> None:
        logger.info(f"[CartPage] Removing item at index {index}")
        self._cart_items().locator(
            "[data-test='delete-product']"
        ).nth(index).click()
        self.wait_for_network_idle(timeout=5_000)

    def remove_item_by_name(self, name: str) -> None:
        logger.info(f"[CartPage] Removing item: {name}")
        row = self._cart_items().filter(has_text=name)
        row.locator("[data-test='delete-product']").click()
        self.wait_for_network_idle(timeout=5_000)

    def clear_cart(self) -> None:
        """Remove all items from the cart."""
        while not self.is_empty() and self._cart_items().locator(
            "[data-test='delete-product']"
        ).count() > 0:
            self.remove_item(0)

    # ── Checkout ──────────────────────────────────────────────────────────────

    def proceed_to_checkout(self) -> None:
        logger.info("[CartPage] Proceeding to checkout")
        self._proceed_to_checkout_btn().click()
        self.wait_for_network_idle()

    # ── Assertions ────────────────────────────────────────────────────────────

    def assert_loaded(self) -> None:
        self.assert_url_contains("/checkout")

    def assert_item_in_cart(self, product_name: str) -> None:
        names = self.get_item_names()
        assert any(product_name.lower() in n.lower() for n in names), (
            f"'{product_name}' not found in cart. Cart contains: {names}"
        )

    def assert_item_count(self, expected: int) -> None:
        actual = self.get_item_count()
        assert actual == expected, f"Expected {expected} cart items, got {actual}"

    def assert_cart_empty(self) -> None:
        assert self.is_empty(), "Expected cart to be empty but it has items"

    def assert_cart_not_empty(self) -> None:
        assert not self.is_empty(), "Expected cart to have items but it is empty"

    def assert_total_is_not_zero(self) -> None:
        total = self.get_cart_total()
        assert "$0.00" not in total, f"Cart total should not be $0.00, got: {total}"

    def assert_proceed_button_visible(self) -> None:
        expect(self._proceed_to_checkout_btn()).to_be_visible()
