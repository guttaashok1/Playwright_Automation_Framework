"""
Visual Regression Testing Utility
===================================
Captures full-page screenshots and compares them against stored baselines
using pixel-level diffing (Pillow). Highlights changed regions in a red
diff image saved to reports/visual_diffs/.

First run  → no baseline exists → screenshot is saved AS the baseline (test passes).
Subsequent → pixel diff is computed; test fails if diff% exceeds threshold.

Usage (via BasePage.assert_visual_match):
    def test_homepage_looks_correct(self, page):
        HomePage(page).open()
        self.assert_visual_match("homepage")   # passes on first run (creates baseline)

CLI: Force-update all baselines:
    pytest --update-baselines

Masking dynamic regions (timestamps, banners):
    self.assert_visual_match("checkout", mask_selectors=[".timestamp", "#live-chat"])
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

from loguru import logger

try:
    from PIL import Image, ImageChops, ImageDraw
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False
    logger.warning(
        "[VisualRegression] Pillow not installed. "
        "Run: pip install Pillow  — visual assertions will be skipped."
    )


class VisualRegression:
    """
    Screenshot-based visual regression tester.

    Args:
        threshold : Maximum allowed pixel-difference ratio (0.0–1.0).
                    Default 0.02 = 2%. Override via VISUAL_THRESHOLD env var.
        baseline_dir : Where baselines are stored (default: test_data/visual_baselines).
        diff_dir     : Where diff images are written (default: reports/visual_diffs).
    """

    def __init__(
        self,
        threshold: float = 0.02,
        baseline_dir: Optional[Path] = None,
        diff_dir: Optional[Path] = None,
    ) -> None:
        import os
        self.threshold = float(os.getenv("VISUAL_THRESHOLD", str(threshold)))
        self.baseline_dir = baseline_dir or Path("test_data/visual_baselines")
        self.diff_dir = diff_dir or Path("reports/visual_diffs")
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.diff_dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ─────────────────────────────────────────────────────────

    def compare(
        self,
        page,
        name: str,
        mask_selectors: list[str] | None = None,
        update_baseline: bool = False,
    ) -> bool:
        """
        Compare current page screenshot against the stored baseline.

        Args:
            page             : Playwright Page object.
            name             : Unique baseline name (e.g. "login_page").
            mask_selectors   : CSS selectors of regions to black-out before diff.
            update_baseline  : If True, overwrite baseline regardless of diff.

        Returns:
            True  → within threshold (or baseline was just created).
            False → diff exceeds threshold (diff image saved to diff_dir).
        """
        if not _PIL_AVAILABLE:
            logger.warning("[VisualRegression] Skipping — Pillow not installed.")
            return True

        baseline_path = self.baseline_dir / f"{name}.png"
        current_bytes = page.screenshot(full_page=True)
        current_img   = Image.open(io.BytesIO(current_bytes)).convert("RGB")

        # Apply masks (blank out dynamic regions)
        if mask_selectors:
            current_img = self._apply_masks(page, current_img, mask_selectors)

        # First run — save as baseline and pass
        if not baseline_path.exists() or update_baseline:
            current_img.save(str(baseline_path))
            action = "Updated" if update_baseline else "Created"
            logger.info(f"[VisualRegression] {action} baseline: {baseline_path}")
            return True

        baseline_img = Image.open(str(baseline_path)).convert("RGB")

        # Resize current to match baseline if viewport changed
        if current_img.size != baseline_img.size:
            logger.warning(
                f"[VisualRegression] Size mismatch for '{name}': "
                f"baseline={baseline_img.size}, current={current_img.size}. Resizing current."
            )
            current_img = current_img.resize(baseline_img.size, Image.LANCZOS)

        diff_ratio, diff_img = self._compute_diff(baseline_img, current_img)
        logger.info(
            f"[VisualRegression] '{name}' — diff={diff_ratio:.4%} "
            f"(threshold={self.threshold:.4%})"
        )

        if diff_ratio > self.threshold:
            diff_path = self.diff_dir / f"{name}_diff.png"
            annotated = self._annotate_diff(baseline_img, current_img, diff_img, diff_ratio)
            annotated.save(str(diff_path))
            logger.error(
                f"[VisualRegression] FAILED '{name}' — diff {diff_ratio:.4%} "
                f"> threshold {self.threshold:.4%}. Diff saved: {diff_path}"
            )
            return False

        return True

    def update_baseline(self, page, name: str) -> None:
        """Force-overwrite the baseline for `name`."""
        self.compare(page, name, update_baseline=True)

    # ── Internal helpers ───────────────────────────────────────────────────

    @staticmethod
    def _compute_diff(
        baseline: "Image.Image", current: "Image.Image"
    ) -> tuple[float, "Image.Image"]:
        """
        Returns (diff_ratio, diff_image).
        diff_ratio is the fraction of pixels that differ beyond a small tolerance.
        """
        diff = ImageChops.difference(baseline, current)
        # Enhance diff for visibility
        diff_enhanced = diff.point(lambda p: 255 if p > 10 else 0)

        total_pixels = baseline.width * baseline.height
        diff_pixels  = sum(1 for p in diff_enhanced.convert("L").getdata() if p > 0)
        ratio        = diff_pixels / total_pixels if total_pixels else 0.0

        return ratio, diff_enhanced

    @staticmethod
    def _annotate_diff(
        baseline: "Image.Image",
        current: "Image.Image",
        diff: "Image.Image",
        ratio: float,
    ) -> "Image.Image":
        """
        Build a side-by-side composite:  Baseline | Current | Diff (red overlay)
        """
        w, h = baseline.width, baseline.height
        composite = Image.new("RGB", (w * 3, h + 30), (30, 30, 30))

        # Labels
        draw = ImageDraw.Draw(composite)
        for i, label in enumerate(["BASELINE", "CURRENT", f"DIFF  ({ratio:.3%})"]):
            draw.text((i * w + 8, 6), label, fill=(255, 255, 255))

        composite.paste(baseline, (0, 30))
        composite.paste(current,  (w, 30))

        # Red-channel diff overlay
        diff_rgb = Image.merge("RGB", (diff.convert("L"), Image.new("L", diff.size, 0), Image.new("L", diff.size, 0)))
        blended  = Image.blend(current, diff_rgb, alpha=0.6)
        composite.paste(blended, (w * 2, 30))

        return composite

    @staticmethod
    def _apply_masks(page, img: "Image.Image", selectors: list[str]) -> "Image.Image":
        """Black-out bounding boxes of all matched elements."""
        draw  = ImageDraw.Draw(img)
        ratio = page.evaluate("window.devicePixelRatio") or 1

        for sel in selectors:
            try:
                boxes = page.locator(sel).evaluate_all(
                    "els => els.map(e => { const r = e.getBoundingClientRect(); "
                    "return {x: r.x, y: r.y, w: r.width, h: r.height}; })"
                )
                for b in boxes:
                    x0 = int(b["x"] * ratio)
                    y0 = int(b["y"] * ratio)
                    x1 = int((b["x"] + b["w"]) * ratio)
                    y1 = int((b["y"] + b["h"]) * ratio)
                    draw.rectangle([x0, y0, x1, y1], fill=(0, 0, 0))
            except Exception as e:
                logger.debug(f"[VisualRegression] Mask selector '{sel}' failed: {e}")

        return img
