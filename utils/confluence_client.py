"""
Confluence Integration Client.

Capabilities:
- Auto-generate Sprint Test Summary pages
- Create/update test documentation pages
- Attach test reports (HTML, screenshots) to Confluence pages
- Search existing pages by title

Usage:
    from utils.confluence_client import ConfluenceClient
    client = ConfluenceClient()
    client.create_or_update_sprint_doc(
        sprint_name="Sprint 42",
        content_html="<h2>Test Results</h2><p>All tests passed.</p>",
    )
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from configs.config import config, ConfluenceConfig


class ConfluenceClient:
    """Client for Atlassian Confluence Cloud REST API."""

    def __init__(self, conf_config: Optional[ConfluenceConfig] = None) -> None:
        cfg = conf_config or config.confluence
        self.base_url = cfg.URL.rstrip("/")
        self.username = cfg.USERNAME
        self.api_token = cfg.API_TOKEN
        self.space_key = cfg.SPACE_KEY

        if not all([self.base_url, self.username, self.api_token]):
            logger.warning("Confluence credentials not configured. Confluence integration disabled.")
            self._enabled = False
            self._confluence = None
        else:
            self._enabled = True
            self._confluence = self._init_client()

    def _init_client(self):
        """Lazy-import atlassian-python-api to avoid hard dependency if not used."""
        try:
            from atlassian import Confluence
            return Confluence(
                url=self.base_url,
                username=self.username,
                password=self.api_token,
                cloud=True,
            )
        except ImportError:
            logger.error("atlassian-python-api not installed. Run: pip install atlassian-python-api")
            self._enabled = False
            return None

    # ------------------------------------------------------------------ #
    # Page management
    # ------------------------------------------------------------------ #

    def get_page_by_title(self, title: str, space_key: Optional[str] = None) -> Optional[dict]:
        """Find a Confluence page by title. Returns page dict or None."""
        if not self._enabled:
            return None
        space = space_key or self.space_key
        page = self._confluence.get_page_by_title(space=space, title=title)
        return page

    def create_page(
        self,
        title: str,
        body_html: str,
        parent_title: Optional[str] = None,
        space_key: Optional[str] = None,
    ) -> dict:
        """Create a new Confluence page."""
        if not self._enabled:
            logger.warning(f"[Confluence] Skipping page creation: {title}")
            return {}

        space = space_key or self.space_key
        parent_id = None
        if parent_title:
            parent = self.get_page_by_title(parent_title, space)
            if parent:
                parent_id = parent["id"]

        result = self._confluence.create_page(
            space=space,
            title=title,
            body=body_html,
            parent_id=parent_id,
            representation="storage",
        )
        page_id = result.get("id", "unknown")
        page_url = f"{self.base_url}/wiki{result.get('_links', {}).get('webui', '')}"
        logger.info(f"[Confluence] Created page: '{title}' (ID: {page_id}) → {page_url}")
        return result

    def update_page(self, page_id: str, title: str, new_body_html: str) -> dict:
        """Update an existing page by ID."""
        if not self._enabled:
            return {}

        # Fetch current version
        current = self._confluence.get_page_by_id(page_id, expand="version")
        version = current["version"]["number"] + 1

        result = self._confluence.update_page(
            page_id=page_id,
            title=title,
            body=new_body_html,
            version=version,
            representation="storage",
        )
        logger.info(f"[Confluence] Updated page '{title}' to version {version}")
        return result

    def create_or_update_page(
        self,
        title: str,
        body_html: str,
        parent_title: Optional[str] = None,
        space_key: Optional[str] = None,
    ) -> dict:
        """Create the page if it doesn't exist, otherwise update it."""
        if not self._enabled:
            return {}

        existing = self.get_page_by_title(title, space_key)
        if existing:
            return self.update_page(existing["id"], title, body_html)
        return self.create_page(title, body_html, parent_title, space_key)

    def attach_file(self, page_id: str, file_path: str, comment: str = "") -> dict:
        """Attach a file (e.g. report, screenshot) to a page."""
        if not self._enabled:
            return {}
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"[Confluence] Attachment file not found: {file_path}")
            return {}
        result = self._confluence.attach_file(
            filename=str(path),
            name=path.name,
            content_type="application/octet-stream",
            page_id=page_id,
            comment=comment,
        )
        logger.info(f"[Confluence] Attached {path.name} to page {page_id}")
        return result

    # ------------------------------------------------------------------ #
    # Test documentation helpers
    # ------------------------------------------------------------------ #

    def create_or_update_sprint_doc(
        self,
        sprint_name: str,
        results: list[dict],
        parent_title: str = "Test Reports",
        space_key: Optional[str] = None,
    ) -> dict:
        """
        Create or update a sprint test summary page.

        Args:
            sprint_name: e.g. "Sprint 42"
            results: List of dicts with keys: name, status, duration, error
            parent_title: Parent page title under which this page lives
        """
        title = f"Test Summary - {sprint_name} - {datetime.now().strftime('%Y-%m-%d')}"
        body_html = self._build_sprint_doc_html(sprint_name, results)
        return self.create_or_update_page(title, body_html, parent_title, space_key)

    def create_test_case_doc(
        self,
        test_name: str,
        steps: list[dict],
        parent_title: str = "Test Cases",
        space_key: Optional[str] = None,
    ) -> dict:
        """
        Create or update a test case documentation page.

        Args:
            test_name: Test case name
            steps: List of dicts with 'action' and 'expectedResult' keys
        """
        title = f"TC: {test_name}"
        body_html = self._build_test_case_html(test_name, steps)
        return self.create_or_update_page(title, body_html, parent_title, space_key)

    # ------------------------------------------------------------------ #
    # HTML builders
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_sprint_doc_html(sprint_name: str, results: list[dict]) -> str:
        passed = sum(1 for r in results if r.get("status") == "passed")
        failed = sum(1 for r in results if r.get("status") == "failed")
        total = len(results)
        pass_rate = round((passed / total * 100) if total else 0, 1)

        rows = ""
        for r in results:
            status_color = "#00875A" if r.get("status") == "passed" else "#DE350B"
            rows += (
                f"<tr>"
                f"<td>{r.get('name', '')}</td>"
                f"<td style='color:{status_color};font-weight:bold'>{r.get('status', '').upper()}</td>"
                f"<td>{r.get('duration', 'N/A')}</td>"
                f"<td>{r.get('error', '')}</td>"
                f"</tr>"
            )

        return f"""
<h1>Test Summary: {sprint_name}</h1>
<p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}</p>
<table>
  <tr>
    <th>Total</th><th>Passed</th><th>Failed</th><th>Pass Rate</th>
  </tr>
  <tr>
    <td>{total}</td>
    <td style='color:#00875A'>{passed}</td>
    <td style='color:#DE350B'>{failed}</td>
    <td>{pass_rate}%</td>
  </tr>
</table>
<h2>Test Results</h2>
<table>
  <tr><th>Test Name</th><th>Status</th><th>Duration</th><th>Error</th></tr>
  {rows}
</table>
"""

    @staticmethod
    def _build_test_case_html(test_name: str, steps: list[dict]) -> str:
        rows = ""
        for i, step in enumerate(steps, start=1):
            rows += (
                f"<tr>"
                f"<td>{i}</td>"
                f"<td>{step.get('action', '')}</td>"
                f"<td>{step.get('expectedResult', '')}</td>"
                f"</tr>"
            )
        return f"""
<h1>Test Case: {test_name}</h1>
<table>
  <tr><th>#</th><th>Action</th><th>Expected Result</th></tr>
  {rows}
</table>
"""
