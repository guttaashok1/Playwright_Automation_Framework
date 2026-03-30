"""
Test Reporter Utility.

Aggregates test results and publishes them to:
- Confluence (sprint docs)
- ADO (test run outcomes)
- Slack (webhook notification)
- Console (summary table)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import requests
from loguru import logger

from configs.config import config
from utils.ado_client import ADOClient, TestOutcome
from utils.confluence_client import ConfluenceClient


@dataclass
class TestResult:
    name: str
    status: str          # "passed" | "failed" | "skipped"
    duration_ms: int = 0
    error: str = ""
    ado_test_case_id: Optional[int] = None


@dataclass
class TestSuiteReport:
    suite_name: str
    environment: str = field(default_factory=lambda: config.get_env())
    results: list[TestResult] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == "passed")

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == "failed")

    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.status == "skipped")

    @property
    def pass_rate(self) -> float:
        return round((self.passed / self.total * 100) if self.total else 0.0, 1)


class TestReporter:
    """
    Orchestrates multi-channel test result reporting.

    Usage (in conftest.py or a pytest plugin):
        reporter = TestReporter()
        reporter.add_result(TestResult(name="test_login", status="passed", duration_ms=1200))
        reporter.publish(
            suite_name="Sprint 42 - Smoke",
            ado_run_id=99,
            sprint_name="Sprint 42",
        )
    """

    def __init__(
        self,
        ado_client: Optional[ADOClient] = None,
        confluence_client: Optional[ConfluenceClient] = None,
    ) -> None:
        self._ado = ado_client or ADOClient()
        self._confluence = confluence_client or ConfluenceClient()
        self._results: list[TestResult] = []

    def add_result(self, result: TestResult) -> None:
        self._results.append(result)

    def publish(
        self,
        suite_name: str,
        ado_run_id: Optional[int] = None,
        sprint_name: Optional[str] = None,
        slack_notify: bool = True,
        teams_notify: bool = False,
    ) -> TestSuiteReport:
        """
        Publish results to all configured channels.
        Returns the built TestSuiteReport.
        """
        report = TestSuiteReport(suite_name=suite_name, results=list(self._results))
        self._print_summary(report)
        self._save_json_report(report)

        if ado_run_id:
            self._push_to_ado(report, ado_run_id)

        if sprint_name:
            self._push_to_confluence(report, sprint_name)

        if slack_notify and config.notification.SLACK_WEBHOOK:
            self._notify_slack(report)

        if teams_notify and config.notification.TEAMS_WEBHOOK:
            self._notify_teams(report)

        return report

    # ------------------------------------------------------------------ #
    # Private — channel publishers
    # ------------------------------------------------------------------ #

    def _print_summary(self, report: TestSuiteReport) -> None:
        separator = "=" * 60
        logger.info(separator)
        logger.info(f"  TEST REPORT: {report.suite_name}")
        logger.info(f"  Environment : {report.environment}")
        logger.info(f"  Total: {report.total}  |  Passed: {report.passed}  |  "
                    f"Failed: {report.failed}  |  Skipped: {report.skipped}  |  "
                    f"Pass Rate: {report.pass_rate}%")
        logger.info(separator)
        for r in report.results:
            icon = "✓" if r.status == "passed" else ("✗" if r.status == "failed" else "○")
            logger.info(f"  {icon}  {r.name}  ({r.duration_ms}ms)")
            if r.error:
                logger.error(f"       └─ {r.error}")
        logger.info(separator)

    def _save_json_report(self, report: TestSuiteReport) -> None:
        output = {
            "suite": report.suite_name,
            "environment": report.environment,
            "started_at": report.started_at,
            "summary": {
                "total": report.total,
                "passed": report.passed,
                "failed": report.failed,
                "skipped": report.skipped,
                "pass_rate": report.pass_rate,
            },
            "results": [
                {
                    "name": r.name,
                    "status": r.status,
                    "duration_ms": r.duration_ms,
                    "error": r.error,
                }
                for r in report.results
            ],
        }
        path = config.reporting.REPORTS_DIR / "results.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(output, indent=2))
        logger.info(f"[Reporter] JSON report saved: {path}")

    def _push_to_ado(self, report: TestSuiteReport, run_id: int) -> None:
        for result in report.results:
            if result.ado_test_case_id:
                outcome = (
                    TestOutcome.PASSED if result.status == "passed"
                    else TestOutcome.FAILED if result.status == "failed"
                    else TestOutcome.NOT_EXECUTED
                )
                self._ado.update_test_result(
                    run_id=run_id,
                    test_case_id=result.ado_test_case_id,
                    outcome=outcome,
                    error_message=result.error or None,
                    duration_ms=result.duration_ms,
                )

    def _push_to_confluence(self, report: TestSuiteReport, sprint_name: str) -> None:
        results_for_confluence = [
            {
                "name": r.name,
                "status": r.status,
                "duration": f"{r.duration_ms}ms",
                "error": r.error,
            }
            for r in report.results
        ]
        self._confluence.create_or_update_sprint_doc(
            sprint_name=sprint_name,
            results=results_for_confluence,
        )

    def _notify_slack(self, report: TestSuiteReport) -> None:
        emoji = ":white_check_mark:" if report.failed == 0 else ":x:"
        message = {
            "channel": config.notification.SLACK_CHANNEL,
            "text": (
                f"{emoji} *{report.suite_name}* — {report.environment.upper()}\n"
                f"> Passed: {report.passed} | Failed: {report.failed} | "
                f"Pass Rate: {report.pass_rate}%"
            ),
        }
        try:
            resp = requests.post(config.notification.SLACK_WEBHOOK, json=message, timeout=10)
            if resp.status_code == 200:
                logger.info("[Reporter] Slack notification sent.")
            else:
                logger.warning(f"[Reporter] Slack webhook returned {resp.status_code}")
        except Exception as e:
            logger.warning(f"[Reporter] Slack notification failed: {e}")

    def _notify_teams(self, report: TestSuiteReport) -> None:
        """Post an MS Teams MessageCard via incoming webhook."""
        theme_color = "00875A" if report.failed == 0 else "DE350B"
        status_icon = "✅" if report.failed == 0 else "❌"
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": f"{report.suite_name} — {report.pass_rate}% passed",
            "sections": [
                {
                    "activityTitle": f"{status_icon} **{report.suite_name}**",
                    "activitySubtitle": f"Environment: `{report.environment.upper()}`",
                    "facts": [
                        {"name": "Total Tests", "value": str(report.total)},
                        {"name": "Passed",      "value": str(report.passed)},
                        {"name": "Failed",      "value": str(report.failed)},
                        {"name": "Skipped",     "value": str(report.skipped)},
                        {"name": "Pass Rate",   "value": f"{report.pass_rate}%"},
                    ],
                    "markdown": True,
                }
            ],
        }
        # Append failed test names if any
        if report.failed > 0:
            failures = [r for r in report.results if r.status == "failed"]
            payload["sections"].append({
                "title": "Failed Tests",
                "facts": [
                    {"name": r.name, "value": r.error[:120] if r.error else "no details"}
                    for r in failures[:10]
                ],
            })
        try:
            resp = requests.post(config.notification.TEAMS_WEBHOOK, json=payload, timeout=10)
            if resp.status_code in (200, 202):
                logger.info("[Reporter] MS Teams notification sent.")
            else:
                logger.warning(f"[Reporter] Teams webhook returned {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.warning(f"[Reporter] Teams notification failed: {e}")
