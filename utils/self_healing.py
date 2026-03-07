"""
Self-Healing Locator Engine
============================
When a primary CSS selector fails to find an element within the timeout,
the engine automatically tries alternative strategies in priority order:

  1. Previously healed selector from registry (fastest — learned from prior runs)
  2. Comma-split variants of the primary selector
  3. Attribute-based CSS (data-testid, id, name, placeholder)
  4. Text / label / placeholder  (Playwright get_by_* helpers)
  5. ARIA role + accessible name
  6. XPath fallbacks

Successful heals are written to configs/healing_registry.json so the
healed selector is tried first on subsequent test runs.

Usage (via BasePage — no direct usage needed):
    # BasePage automatically wraps every page.locator() call
    # Direct usage:
    from utils.self_healing import SelfHealingLocator
    locator = SelfHealingLocator(page, "[data-testid='btn']", "Submit button").find()
    locator.click()
"""
from __future__ import annotations

import hashlib
import json
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger
from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError


# ── Registry ──────────────────────────────────────────────────────────────────

class HealingRegistry:
    """
    Persistent JSON store for healed selector mappings.
    Key   : SHA-1 of (page_url_pattern + original_selector)
    Value : { healed_selector, original_selector, heal_count, first_healed_at, last_healed_at }
    """

    REGISTRY_FILE = Path(__file__).parent.parent / "configs" / "healing_registry.json"

    @classmethod
    def load(cls) -> dict:
        if cls.REGISTRY_FILE.exists():
            try:
                return json.loads(cls.REGISTRY_FILE.read_text())
            except Exception:
                return {}
        return {}

    @classmethod
    def save(cls, data: dict) -> None:
        cls.REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write via temp file
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=cls.REGISTRY_FILE.parent,
            delete=False,
            suffix=".tmp",
        ) as tmp:
            json.dump(data, tmp, indent=2)
            tmp_path = Path(tmp.name)
        tmp_path.replace(cls.REGISTRY_FILE)

    @classmethod
    def make_key(cls, selector: str, caller_key: str = "") -> str:
        raw = f"{caller_key}::{selector}"
        return hashlib.sha1(raw.encode()).hexdigest()[:12]

    @classmethod
    def get_healed(cls, selector: str, caller_key: str = "") -> Optional[str]:
        key = cls.make_key(selector, caller_key)
        data = cls.load()
        entry = data.get(key)
        if entry:
            return entry["healed_selector"]
        return None

    @classmethod
    def record_heal(cls, selector: str, healed_selector: str, caller_key: str = "") -> None:
        key = cls.make_key(selector, caller_key)
        data = cls.load()
        now = datetime.utcnow().isoformat() + "Z"
        existing = data.get(key, {})
        data[key] = {
            "original_selector": selector,
            "healed_selector": healed_selector,
            "caller_key": caller_key,
            "heal_count": existing.get("heal_count", 0) + 1,
            "first_healed_at": existing.get("first_healed_at", now),
            "last_healed_at": now,
        }
        cls.save(data)
        logger.warning(
            f"[Self-Heal] Recorded healing: {selector!r} → {healed_selector!r} "
            f"(key={key}, total_heals={data[key]['heal_count']})"
        )

    @classmethod
    def summary(cls) -> dict:
        data = cls.load()
        return {
            "total_entries": len(data),
            "entries": [
                {
                    "original": v["original_selector"],
                    "healed_to": v["healed_selector"],
                    "heal_count": v["heal_count"],
                }
                for v in data.values()
            ],
        }


# ── Self-Healing Locator ───────────────────────────────────────────────────────

# Short probe timeout — used when trying fallback selectors so we fail fast
_PROBE_TIMEOUT_MS = 3_000


class SelfHealingLocator:
    """
    Wraps a Playwright Page + selector string.
    Call .find() to get a working Locator (or raise with a detailed healing log).
    """

    def __init__(
        self,
        page: Page,
        selector: str,
        element_name: str = "",
        timeout: int = 30_000,
        caller_key: str = "",
    ) -> None:
        self.page = page
        self.selector = selector
        self.element_name = element_name or selector
        self.timeout = timeout
        self.caller_key = caller_key

    # ── Public API ────────────────────────────────────────────────────────────

    def find(self, state: str = "visible") -> Locator:
        """
        Try primary selector first (full timeout).
        On failure, iterate through healing strategies with short probe timeout.
        Returns a confirmed-visible Locator or raises PlaywrightTimeoutError.
        """
        # 1. Try previously healed selector first (skip heavy probing)
        healed = HealingRegistry.get_healed(self.selector, self.caller_key)
        if healed and healed != self.selector:
            loc = self._try_selector(healed, state)
            if loc:
                logger.debug(f"[Self-Heal] Using cached healed selector: {healed!r}")
                return loc

        # 2. Try primary selector
        loc = self._try_selector(self.selector, state, timeout=self.timeout)
        if loc:
            return loc

        logger.warning(
            f"[Self-Heal] Primary selector failed: {self.selector!r} "
            f"(element={self.element_name!r}). Starting healing..."
        )

        # 3. Try all generated fallback strategies
        attempted: list[str] = []
        for fallback in self._generate_fallbacks():
            if fallback == self.selector or fallback in attempted:
                continue
            attempted.append(fallback)
            loc = self._try_selector(fallback, state)
            if loc:
                logger.warning(
                    f"[Self-Heal] ✓ Healed {self.element_name!r}: "
                    f"{self.selector!r} → {fallback!r}"
                )
                HealingRegistry.record_heal(self.selector, fallback, self.caller_key)
                return loc

        # 4. All strategies exhausted — raise with context
        raise PlaywrightTimeoutError(
            f"Self-healing failed for element '{self.element_name}'.\n"
            f"  Primary selector : {self.selector!r}\n"
            f"  Strategies tried : {len(attempted)}\n"
            f"  Fallbacks tried  : {attempted[:10]}\n"
            f"  Page URL         : {self.page.url}"
        )

    # ── Fallback strategy generator ───────────────────────────────────────────

    def _generate_fallbacks(self) -> list[str]:
        """
        Build ordered list of fallback selectors from the primary selector.
        Strategy priority:
          1. Comma-split variants (already common in this codebase)
          2. data-testid extracted from primary
          3. id / name / placeholder attribute CSS
          4. Playwright role/text/placeholder helpers (as CSS-like strings)
          5. XPath by attribute
        """
        fallbacks: list[str] = []
        primary = self.selector.strip()

        # --- Strategy 1: comma-split variants (e.g. "sel1, sel2, sel3") ---
        parts = [p.strip() for p in primary.split(",") if p.strip() and p.strip() != primary]
        fallbacks.extend(parts)

        # --- Strategy 2: extract attribute values from primary selector ---
        attrs = self._extract_attributes(primary)

        if attrs.get("data-testid"):
            tid = attrs["data-testid"]
            fallbacks.append(f"[data-testid='{tid}']")
            fallbacks.append(f"[data-testid=\"{tid}\"]")

        if attrs.get("id"):
            fallbacks.append(f"#{attrs['id']}")

        if attrs.get("name"):
            n = attrs["name"]
            fallbacks.append(f"[name='{n}']")
            fallbacks.append(f"input[name='{n}']")

        if attrs.get("placeholder"):
            ph = attrs["placeholder"]
            fallbacks.append(f"[placeholder='{ph}']")
            fallbacks.append(f"[placeholder*='{ph[:15]}']")

        if attrs.get("type"):
            fallbacks.append(f"input[type='{attrs['type']}']")

        # --- Strategy 3: role-based selectors inferred from selector structure ---
        if "submit" in primary.lower() or "button" in primary.lower():
            fallbacks += [
                "button[type='submit']",
                "[role='button']",
                "input[type='submit']",
            ]

        if "input[type='email']" not in fallbacks and "email" in primary.lower():
            fallbacks.append("input[type='email']")

        if "input[type='password']" not in fallbacks and "password" in primary.lower():
            fallbacks.append("input[type='password']")

        if "checkbox" in primary.lower():
            fallbacks.append("input[type='checkbox']")

        # --- Strategy 4: tag-only fallbacks for simple selectors ---
        tag_match = re.match(r'^(\w+)$', primary)
        if tag_match:
            fallbacks.append(f"{primary}:first-of-type")

        # --- Strategy 5: relaxed class selector (first class only) ---
        class_match = re.findall(r'\.([\w-]+)', primary)
        if class_match:
            fallbacks.append(f"[class*='{class_match[0]}']")

        # --- Strategy 6: aria-label variations ---
        aria_match = re.search(r'\[aria-label=["\']([^"\']+)["\']', primary)
        if aria_match:
            label = aria_match.group(1)
            fallbacks.append(f"[aria-label*='{label[:20]}']")

        # Deduplicate while preserving order
        seen: set[str] = {primary}
        return [f for f in fallbacks if f not in seen and not seen.add(f)]  # type: ignore

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _try_selector(
        self, selector: str, state: str, timeout: Optional[int] = None
    ) -> Optional[Locator]:
        """
        Returns a Playwright Locator if visible within timeout, else None.
        Uses a short probe timeout for fallback candidates to fail fast.
        """
        t = timeout if timeout is not None else _PROBE_TIMEOUT_MS
        try:
            loc = self.page.locator(selector)
            loc.first.wait_for(state=state, timeout=t)
            return loc.first
        except Exception:
            return None

    @staticmethod
    def _extract_attributes(selector: str) -> dict[str, str]:
        """Parse attribute values from a CSS selector string."""
        attrs: dict[str, str] = {}
        patterns = {
            "data-testid": r'\[data-testid=["\']([^"\']+)["\']',
            "id": r'#([\w-]+)',
            "name": r'\[name=["\']([^"\']+)["\']',
            "placeholder": r'\[placeholder=["\']([^"\']+)["\']',
            "type": r'\[type=["\']([^"\']+)["\']|input\[type=["\']([^"\']+)["\']',
            "aria-label": r'\[aria-label=["\']([^"\']+)["\']',
        }
        for attr, pattern in patterns.items():
            m = re.search(pattern, selector)
            if m:
                attrs[attr] = next(g for g in m.groups() if g)
        return attrs
