"""
Page Object: Practice Software Testing — Shopping Cart Page
URL: https://practicesoftwaretesting.com/checkout
"""
from __future__ import annotations

from loguru import logger
from playwright.sync_api import Page

from pages.base_page import BasePage


class PracticeCartPage(BasePage):
    """Shopping cart page — view, update quantity, remove items, proceed."""

    # ── Selectors ────────────────────────────────────────────────────────────
    _CART_ITEMS           = "[data-test='cart-item']"
    _ITEM_TITLE           = "[data-test='product-title']"
    _ITEM_PRICE           = "[data-test='product-price']"
    _ITEM_QTY_INPUT       = "[data-test='product-quantity']"
    _ITEM_LINE_TOTAL      = "[data-test='line-price']"
    _ITEM_REMOVE_BTN      = "[data-test='delete-product']"
    _CART_TOTAL           = "[data-test='cart-total']"
    _PROCEED_TO_CHECKOUT  = "[data-test='proceed-1']"
    _EMPTY_CART_MESSAGE   = "[data-test='empty-cart']"
    _CART_TITLE           = "h2"
    _NAV_CART             = "[data-test='nav-cart']"
    _TOAST_MESSAGE        = ".toast-body"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.url = "https://practicesoftwaretesting.com/checkout"

    # ── Navigation ────────────────────────────────────────────────────────────

    def open(self) -> "PracticeCartPage":
        logger.info("[CartPage] Opening cart")
        self.navigate_to_url(self.url)
        self.wait_for_network_idle()
        return self

    def open_via_navbar(self) -> "PracticeCartPage":
        self.click(self._NAV_CART)
        self.wait_for_network_idle()
        return self

    # ── Cart Contents ─────────────────────────────────────────────────────────

    def get_item_count(self) -> int:
        return self.element_count(self._CART_ITEMS)

    def get_item_names(self) -> list[str]:
        return self.page.locator(f"{self._CART_ITEMS} {self._ITEM_TITLE}").all_inner_texts()

    def get_item_prices(self) -> list[str]:
        return self.page.locator(f"{self._CART_ITEMS} {self._ITEM_PRICE}").all_inner_texts()

    def get_item_quantities(self) -> list[int]:
        items = self.page.locator(f"{self._CART_ITEMS} {self._ITEM_QTY_INPUT}").all()
        return [int(item.input_value()) for item in items]

    def get_cart_total(self) -> str:
        return self.get_text(self._CART_TOTAL)

    def is_empty(self) -> bool:
        return self.is_visible(self._EMPTY_CART_MESSAGE)

    # ── Item Operations ───────────────────────────────────────────────────────

    def update_item_quantity(self, index: int, qty: int) -> None:
        logger.info(f"[CartPage] Updating item {index} quantity to {qty}")
        qty_loc = self.page.locator(f"{self._CART_ITEMS} {self._ITEM_QTY_INPUT}").nth(index)
        qty_loc.clear()
        qty_loc.fill(str(qty))
        qty_loc.press("Tab")           # trigger blur/change event
        self.wait_for_network_idle(timeout=5_000)

    def remove_item(self, index: int = 0) -> None:
        logger.info(f"[CartPage] Removing item at index {index}")
        self.page.locator(f"{self._CART_ITEMS} {self._ITEM_REMOVE_BTN}").nth(index).click()
        self.wait_for_network_idle(timeout=5_000)

    def remove_item_by_name(self, name: str) -> None:
        logger.info(f"[CartPage] Removing item: {name}")
        row = self.page.locator(self._CART_ITEMS).filter(has_text=name)
        row.locator(self._ITEM_REMOVE_BTN).click()
        self.wait_for_network_idle(timeout=5_000)

    def clear_cart(self) -> None:
        """Remove all items from the cart."""
        while not self.is_empty() and self.element_count(self._ITEM_REMOVE_BTN) > 0:
            self.remove_item(0)

    # ── Checkout ──────────────────────────────────────────────────────────────

    def proceed_to_checkout(self) -> None:
        logger.info("[CartPage] Proceeding to checkout")
        self.click(self._PROCEED_TO_CHECKOUT)
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
        self.assert_visible(self._PROCEED_TO_CHECKOUT)
