"""
Azure DevOps (ADO) Integration Client.

Capabilities:
- Fetch test cases from a Test Plan/Suite
- Create new test cases programmatically
- Update test case steps and expected results
- Record test run outcomes (Passed/Failed/Blocked)
- Link test cases to User Stories / Work Items

Usage:
    from utils.ado_client import ADOClient
    client = ADOClient()
    client.update_test_result(test_case_id=1001, outcome="Passed")
"""
from __future__ import annotations

import base64
from datetime import datetime
from typing import Optional

import requests
from loguru import logger

from configs.config import config, ADOConfig


# ADO outcome mapping
class TestOutcome:
    PASSED = "Passed"
    FAILED = "Failed"
    BLOCKED = "Blocked"
    NOT_EXECUTED = "NotExecuted"
    IN_PROGRESS = "InProgress"


class ADOClient:
    """Client for Azure DevOps Test Management APIs."""

    def __init__(self, ado_config: Optional[ADOConfig] = None) -> None:
        cfg = ado_config or config.ado
        self.org_url = cfg.ORG_URL.rstrip("/")
        self.project = cfg.PROJECT
        self.pat = cfg.PAT
        self.default_test_plan_id = cfg.TEST_PLAN_ID

        if not all([self.org_url, self.project, self.pat]):
            logger.warning("ADO credentials not fully configured. ADO integration disabled.")
            self._enabled = False
        else:
            self._enabled = True
            self._auth_header = self._build_auth_header()

    def _build_auth_header(self) -> dict:
        token = base64.b64encode(f":{self.pat}".encode()).decode()
        return {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        }

    def _get(self, url: str, params: Optional[dict] = None) -> dict:
        response = requests.get(url, headers=self._auth_header, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def _post(self, url: str, payload: dict) -> dict:
        response = requests.post(url, headers=self._auth_header, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def _patch(self, url: str, payload: list | dict, content_type: Optional[str] = None) -> dict:
        headers = dict(self._auth_header)
        if content_type:
            headers["Content-Type"] = content_type
        response = requests.patch(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------ #
    # Test Plans & Suites
    # ------------------------------------------------------------------ #

    def get_test_plans(self) -> list[dict]:
        """List all test plans in the project."""
        if not self._enabled:
            return []
        url = f"{self.org_url}/{self.project}/_apis/testplan/plans?api-version=7.1"
        result = self._get(url)
        return result.get("value", [])

    def get_test_suites(self, plan_id: int) -> list[dict]:
        """List all test suites in a test plan."""
        if not self._enabled:
            return []
        url = f"{self.org_url}/{self.project}/_apis/testplan/Plans/{plan_id}/suites?api-version=7.1"
        result = self._get(url)
        return result.get("value", [])

    def get_test_cases(self, plan_id: int, suite_id: int) -> list[dict]:
        """List all test cases in a test suite."""
        if not self._enabled:
            return []
        url = (
            f"{self.org_url}/{self.project}/_apis/testplan/Plans/{plan_id}"
            f"/Suites/{suite_id}/TestCase?api-version=7.1"
        )
        result = self._get(url)
        return result.get("value", [])

    # ------------------------------------------------------------------ #
    # Work Items (Test Cases are Work Items in ADO)
    # ------------------------------------------------------------------ #

    def get_test_case(self, test_case_id: int) -> dict:
        """Fetch a single work item (test case) by ID."""
        if not self._enabled:
            return {}
        url = f"{self.org_url}/_apis/wit/workitems/{test_case_id}?api-version=7.1"
        return self._get(url)

    def create_test_case(
        self,
        title: str,
        steps: list[dict],
        area_path: Optional[str] = None,
        iteration_path: Optional[str] = None,
        linked_user_story_id: Optional[int] = None,
    ) -> dict:
        """
        Create a new Test Case work item.

        Args:
            title: Test case title
            steps: List of dicts with 'action' and 'expectedResult' keys
            area_path: ADO area path (defaults to project name)
            iteration_path: ADO iteration / sprint path
            linked_user_story_id: Link this test case to a User Story

        Returns:
            Created work item dict
        """
        if not self._enabled:
            logger.warning("ADO not configured — skipping create_test_case")
            return {}

        steps_xml = self._build_steps_xml(steps)

        patch_document = [
            {"op": "add", "path": "/fields/System.Title", "value": title},
            {"op": "add", "path": "/fields/System.AreaPath", "value": area_path or self.project},
            {"op": "add", "path": "/fields/Microsoft.VSTS.TCM.Steps", "value": steps_xml},
        ]
        if iteration_path:
            patch_document.append(
                {"op": "add", "path": "/fields/System.IterationPath", "value": iteration_path}
            )

        url = (
            f"{self.org_url}/{self.project}/_apis/wit/workitems/$Test%20Case"
            "?api-version=7.1"
        )
        result = self._patch(url, patch_document, content_type="application/json-patch+json")
        test_case_id = result["id"]
        logger.info(f"[ADO] Created Test Case #{test_case_id}: {title}")

        if linked_user_story_id:
            self.link_to_user_story(test_case_id, linked_user_story_id)

        return result

    def update_test_case_title(self, test_case_id: int, new_title: str) -> dict:
        """Update the title of an existing test case."""
        if not self._enabled:
            return {}
        url = f"{self.org_url}/_apis/wit/workitems/{test_case_id}?api-version=7.1"
        patch = [{"op": "replace", "path": "/fields/System.Title", "value": new_title}]
        result = self._patch(url, patch, content_type="application/json-patch+json")
        logger.info(f"[ADO] Updated Test Case #{test_case_id} title to: {new_title}")
        return result

    def link_to_user_story(self, test_case_id: int, user_story_id: int) -> None:
        """Add a 'Tested By' link between a test case and a User Story."""
        if not self._enabled:
            return
        url = f"{self.org_url}/_apis/wit/workitems/{test_case_id}?api-version=7.1"
        user_story_url = f"{self.org_url}/_apis/wit/workitems/{user_story_id}"
        patch = [
            {
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": "Microsoft.VSTS.Common.TestedBy-Reverse",
                    "url": user_story_url,
                    "attributes": {"comment": "Linked by automation framework"},
                },
            }
        ]
        self._patch(url, patch, content_type="application/json-patch+json")
        logger.info(f"[ADO] Linked Test Case #{test_case_id} to User Story #{user_story_id}")

    # ------------------------------------------------------------------ #
    # Test Runs & Results
    # ------------------------------------------------------------------ #

    def create_test_run(
        self,
        name: str,
        plan_id: Optional[int] = None,
        build_id: Optional[str] = None,
    ) -> int:
        """Create a new test run. Returns the run ID."""
        if not self._enabled:
            return 0
        url = f"{self.org_url}/{self.project}/_apis/test/runs?api-version=7.1"
        payload = {
            "name": name,
            "plan": {"id": plan_id or self.default_test_plan_id},
            "isAutomated": True,
            "startedDate": datetime.utcnow().isoformat() + "Z",
        }
        if build_id:
            payload["build"] = {"id": build_id}

        result = self._post(url, payload)
        run_id = result["id"]
        logger.info(f"[ADO] Created Test Run #{run_id}: {name}")
        return run_id

    def update_test_result(
        self,
        run_id: int,
        test_case_id: int,
        outcome: str,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> None:
        """
        Update a test result inside a run.

        Args:
            run_id: ADO test run ID
            test_case_id: ADO test case work item ID
            outcome: One of TestOutcome constants
            error_message: Failure message if outcome is Failed
            duration_ms: Test execution duration in milliseconds
        """
        if not self._enabled:
            return

        url = f"{self.org_url}/{self.project}/_apis/test/runs/{run_id}/results?api-version=7.1"
        result_payload: dict = {
            "testCaseId": test_case_id,
            "outcome": outcome,
            "completedDate": datetime.utcnow().isoformat() + "Z",
        }
        if error_message:
            result_payload["errorMessage"] = error_message
        if duration_ms is not None:
            result_payload["durationInMs"] = duration_ms

        self._post(url, [result_payload])
        logger.info(f"[ADO] Test Case #{test_case_id} → {outcome} (Run #{run_id})")

    def complete_test_run(self, run_id: int) -> None:
        """Mark a test run as completed."""
        if not self._enabled:
            return
        url = f"{self.org_url}/{self.project}/_apis/test/runs/{run_id}?api-version=7.1"
        patch = [{"op": "replace", "path": "/state", "value": "Completed"}]
        self._patch(url, patch, content_type="application/json-patch+json")
        logger.info(f"[ADO] Completed Test Run #{run_id}")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_steps_xml(steps: list[dict]) -> str:
        """Convert a list of step dicts to ADO XML test step format."""
        step_items = ""
        for i, step in enumerate(steps, start=1):
            action = step.get("action", "")
            expected = step.get("expectedResult", "")
            step_items += (
                f'<step id="{i}" type="ActionStep">'
                f"<parameterizedString isformatted=\"true\">{action}</parameterizedString>"
                f"<parameterizedString isformatted=\"true\">{expected}</parameterizedString>"
                f"</step>"
            )
        return f"<steps id='0' last='{len(steps)}'>{step_items}</steps>"
