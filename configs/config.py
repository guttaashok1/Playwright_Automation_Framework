"""
Central configuration management.
Reads from environment variables (via .env) with sensible defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")


class AppConfig:
    """Application under test configuration."""

    BASE_URL: str = os.getenv("BASE_URL", "https://practicesoftwaretesting.com")
    API_BASE_URL: str = os.getenv("API_BASE_URL", "https://api.practicesoftwaretesting.com")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "test")


class BrowserConfig:
    """Playwright browser configuration."""

    BROWSER: str = os.getenv("BROWSER", "chromium")
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() == "true"
    SLOW_MO: int = int(os.getenv("SLOW_MO", "0"))
    VIEWPORT_WIDTH: int = int(os.getenv("VIEWPORT_WIDTH", "1920"))
    VIEWPORT_HEIGHT: int = int(os.getenv("VIEWPORT_HEIGHT", "1080"))

    # Timeouts (milliseconds)
    DEFAULT_TIMEOUT: int = 30_000
    NAVIGATION_TIMEOUT: int = 60_000
    ELEMENT_TIMEOUT: int = 15_000


class TestCredentials:
    """Test user credentials."""

    EMAIL: str = os.getenv("TEST_USER_EMAIL", "customer@practicesoftwaretesting.com")
    PASSWORD: str = os.getenv("TEST_USER_PASSWORD", "welcome01")
    ADMIN_EMAIL: str = os.getenv("TEST_ADMIN_EMAIL", "admin@practicesoftwaretesting.com")
    ADMIN_PASSWORD: str = os.getenv("TEST_ADMIN_PASSWORD", "AQw3j6wBY")


class ADOConfig:
    """Azure DevOps configuration."""

    ORG_URL: str = os.getenv("ADO_ORG_URL", "")
    PROJECT: str = os.getenv("ADO_PROJECT", "")
    PAT: str = os.getenv("ADO_PAT", "")
    TEST_PLAN_ID: int = int(os.getenv("ADO_TEST_PLAN_ID", "0"))


class ConfluenceConfig:
    """Confluence configuration."""

    URL: str = os.getenv("CONFLUENCE_URL", "")
    USERNAME: str = os.getenv("CONFLUENCE_USERNAME", "")
    API_TOKEN: str = os.getenv("CONFLUENCE_API_TOKEN", "")
    SPACE_KEY: str = os.getenv("CONFLUENCE_SPACE_KEY", "QA")


class ReportingConfig:
    """Reporting configuration."""

    REPORTS_DIR: Path = Path(__file__).parent.parent / "reports"
    ALLURE_RESULTS_DIR: Path = REPORTS_DIR / "allure-results"
    ARTIFACTS_DIR: Path = REPORTS_DIR / "artifacts"
    SLACK_WEBHOOK: str = os.getenv("SLACK_WEBHOOK_URL", "")
    SLACK_CHANNEL: str = os.getenv("SLACK_CHANNEL", "#test-results")


class NotificationConfig:
    """Slack + MS Teams webhook configuration."""

    SLACK_WEBHOOK: str = os.getenv("SLACK_WEBHOOK_URL", "")
    SLACK_CHANNEL: str = os.getenv("SLACK_CHANNEL", "#test-results")
    TEAMS_WEBHOOK: str = os.getenv("TEAMS_WEBHOOK_URL", "")


class SelfHealingConfig:
    """Self-healing locator configuration."""

    ENABLED: bool = os.getenv("SELF_HEALING_ENABLED", "true").lower() == "true"
    PROBE_TIMEOUT_MS: int = int(os.getenv("SELF_HEALING_PROBE_TIMEOUT_MS", "3000"))
    REGISTRY_FILE: Path = Path(__file__).parent / "healing_registry.json"


class VisualConfig:
    """Visual regression configuration."""

    ENABLED: bool = os.getenv("VISUAL_REGRESSION_ENABLED", "true").lower() == "true"
    THRESHOLD: float = float(os.getenv("VISUAL_THRESHOLD", "0.02"))
    BASELINE_DIR: Path = Path(__file__).parent.parent / "test_data" / "visual_baselines"
    DIFF_DIR: Path = Path(__file__).parent.parent / "reports" / "visual_diffs"


class Config:
    """Unified configuration object."""

    app = AppConfig()
    browser = BrowserConfig()
    credentials = TestCredentials()
    ado = ADOConfig()
    confluence = ConfluenceConfig()
    reporting = ReportingConfig()
    notification = NotificationConfig()
    self_healing = SelfHealingConfig()
    visual = VisualConfig()

    @classmethod
    def is_ci(cls) -> bool:
        """Detect if running inside CI/CD (GitHub Actions, etc.)."""
        return os.getenv("CI", "false").lower() == "true"

    @classmethod
    def get_env(cls) -> str:
        return AppConfig.ENVIRONMENT


# Singleton
config = Config()
