# Playwright Automation Framework

End-to-End STLC automation framework using **Python + Playwright** with integrations for **Azure DevOps**, **Confluence**, and **GitHub Actions CI/CD**.

```
Design → Task → Docs → Test → PR: Seamless, Prompt-Driven Pipeline
```

---

## Architecture

```
playwright_automation/
├── .github/
│   └── workflows/
│       └── playwright-tests.yml     # CI/CD: lint → API tests → UI tests (matrix) → publish
├── configs/
│   └── config.py                    # Centralised config (reads from .env)
├── pages/
│   ├── base_page.py                 # Base POM: clicks, fills, waits, assertions
│   ├── login_page.py                # Login page object
│   └── dashboard_page.py            # Dashboard page object
├── tests/
│   ├── ui/
│   │   ├── test_login.py            # UI: login flows
│   │   └── test_dashboard.py        # UI: dashboard
│   └── api/
│       └── test_auth_api.py         # API: auth + users endpoints
├── utils/
│   ├── api_client.py                # HTTP client (httpx) with retries & logging
│   ├── ado_client.py                # Azure DevOps: test cases, runs, results
│   ├── confluence_client.py         # Confluence: sprint docs, test case pages
│   └── reporter.py                  # Multi-channel reporter (ADO + Confluence + Slack)
├── reports/                         # Generated test output (gitignored)
├── conftest.py                      # Pytest fixtures: page, authenticated_page, API/ADO/Confluence clients
├── pytest.ini                       # Pytest settings & markers
├── requirements.txt                 # Python dependencies
└── .env.example                     # Environment variable template
```

---

## Quick Start

### 1. Prerequisites

- Python 3.10+
- pip

### 2. Install dependencies

```bash
pip install -r requirements.txt
playwright install --with-deps chromium
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your values:
#   BASE_URL, API_BASE_URL, TEST_USER_EMAIL/PASSWORD
#   ADO_ORG_URL, ADO_PROJECT, ADO_PAT
#   CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN
```

### 4. Run tests

```bash
# Smoke tests (fast — critical paths only)
pytest -m smoke

# All UI tests
pytest -m ui

# All API tests
pytest -m api

# Full regression
pytest -m regression

# Specific browser
pytest --browser=firefox -m ui

# Headed mode (see the browser)
pytest --headed -m smoke

# Parallel execution
pytest -n 4 -m regression
```

---

## Test Markers

| Marker       | Description                                  |
|-------------|----------------------------------------------|
| `smoke`     | Fast, critical path tests — run on every PR  |
| `regression`| Full regression suite — run nightly          |
| `ui`        | Browser/Playwright tests                     |
| `api`       | Direct REST API tests                        |
| `ado`       | Tests linked to ADO test cases               |
| `slow`      | Tests expected to take longer than average   |

---

## Integrations

### Azure DevOps (ADO)

The `ADOClient` (`utils/ado_client.py`) supports:

- **Fetch** test plans, suites, and test cases
- **Create** new test cases linked to User Stories
- **Record** test run outcomes (Passed/Failed/Blocked)
- **Link** test cases to sprints / work items

Configure via `.env`:
```
ADO_ORG_URL=https://dev.azure.com/your-org
ADO_PROJECT=YourProject
ADO_PAT=your_personal_access_token
```

To update a result programmatically:
```python
from utils.ado_client import ADOClient, TestOutcome
client = ADOClient()
run_id = client.create_test_run("Sprint 42 - Smoke")
client.update_test_result(run_id, test_case_id=1001, outcome=TestOutcome.PASSED)
client.complete_test_run(run_id)
```

### Confluence

The `ConfluenceClient` (`utils/confluence_client.py`) supports:

- **Auto-generate** sprint test summary pages
- **Create/update** test case documentation pages
- **Attach** HTML reports and screenshots

Configure via `.env`:
```
CONFLUENCE_URL=https://your-org.atlassian.net
CONFLUENCE_USERNAME=your_email@example.com
CONFLUENCE_API_TOKEN=your_api_token
CONFLUENCE_SPACE_KEY=QA
```

### GitHub Actions CI/CD

The workflow (`.github/workflows/playwright-tests.yml`):

| Job               | Trigger              | Description                              |
|-------------------|----------------------|------------------------------------------|
| `lint`            | All triggers         | ruff + mypy static analysis              |
| `api-tests`       | All triggers         | REST API tests                           |
| `ui-tests`        | All triggers         | Playwright UI — matrix: chromium/firefox/webkit |
| `publish-results` | After tests complete | Push results to ADO + Confluence + Slack |
| `pr-status`       | Pull Requests        | Post test summary comment on the PR      |

**Required GitHub Secrets:**
```
BASE_URL, API_BASE_URL
TEST_USER_EMAIL, TEST_USER_PASSWORD
ADO_ORG_URL, ADO_PROJECT, ADO_PAT
CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN
SLACK_WEBHOOK_URL  (optional)
```

---

## Adding a New Page

1. Create `pages/my_feature_page.py` extending `BasePage`
2. Define selectors as class attributes
3. Implement action methods
4. Add tests in `tests/ui/test_my_feature.py`

```python
from pages.base_page import BasePage

class MyFeaturePage(BasePage):
    _SUBMIT_BUTTON = "[data-testid='submit']"

    def submit_form(self, data: dict) -> None:
        self.fill("#name", data["name"])
        self.click(self._SUBMIT_BUTTON)
```

---

## Reports

After a test run, reports are in the `reports/` directory:

| File                    | Description                    |
|-------------------------|-------------------------------|
| `reports/report.html`   | pytest-html summary report    |
| `reports/results.json`  | Machine-readable JSON results |
| `reports/pytest.log`    | Full debug log                |
| `reports/artifacts/`    | Screenshots, videos, traces   |

---

## Troubleshooting

**Playwright browser not found:**
```bash
playwright install chromium
```

**Import errors:**
```bash
pip install -r requirements.txt
```

**ADO/Confluence calls silently skipped:**
Check that `.env` contains valid credentials. The clients log a warning and no-op when not configured.
