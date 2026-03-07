"""
End-to-End Automation: Register & Login on practicesoftwaretesting.com
Steps:
  1. Navigate to https://practicesoftwaretesting.com/
  2. Click "Sign In"
  3. Click "Register your account"
  4. Fill and submit the registration form
  5. Login with the newly registered credentials
"""
import re
import time
import pytest
from faker import Faker
from playwright.sync_api import Page, sync_playwright, expect

# ── Test data (module-scoped so the same values are reused across steps) ──
fake = Faker()
FIRST_NAME    = fake.first_name()
LAST_NAME     = fake.last_name()
EMAIL         = f"testuser_{fake.unique.random_int(min=10000, max=99999)}@mailinator.com"
PASSWORD      = f"Pw!{fake.unique.random_int(min=100000, max=999999)}#Aq"
DOB           = "1990-01-15"
PHONE         = fake.numerify("##########")
STREET        = fake.street_address()
CITY          = fake.city()
STATE         = fake.state()
POSTCODE      = fake.zipcode()
COUNTRY_VALUE = "US"

BASE_URL = "https://practicesoftwaretesting.com"


@pytest.mark.ui
@pytest.mark.smoke
class TestPracticeRegistrationAndLogin:
    """
    End-to-end test: register a new account and log in with it
    on practicesoftwaretesting.com (Tool Shop v5).
    """

    def test_step1_navigate_to_home(self, page: Page):
        """Step 1 — Home page loads successfully."""
        page.goto(BASE_URL, wait_until="networkidle")
        expect(page).to_have_title(re.compile(r"Toolshop|Practice", re.IGNORECASE))

    def test_step2_click_sign_in(self, page: Page):
        """Step 2 — Sign In link navigates to the login page."""
        page.goto(BASE_URL, wait_until="networkidle")
        page.get_by_role("link", name="Sign in").click()
        page.wait_for_url("**/auth/login**", timeout=15_000)
        expect(page).to_have_url(re.compile(r"/auth/login"))

    def test_step3_navigate_to_register(self, page: Page):
        """Step 3 — 'Register your account' link reaches the registration page."""
        page.goto(f"{BASE_URL}/auth/login", wait_until="networkidle")
        page.get_by_role("link", name="Register your account").click()
        page.wait_for_url("**/auth/register**", timeout=15_000)
        expect(page).to_have_url(re.compile(r"/auth/register"))

    def test_step4_register_new_user(self, page: Page):
        """Step 4 — Fill registration form with generated data and submit."""
        page.goto(f"{BASE_URL}/auth/register", wait_until="networkidle")

        page.get_by_placeholder("First name *").fill(FIRST_NAME)
        page.get_by_placeholder("Your last name *").fill(LAST_NAME)
        page.get_by_placeholder("YYYY-MM-DD").fill(DOB)
        page.get_by_placeholder("Your Street *").fill(STREET)
        page.get_by_placeholder("Your Postcode *").fill(POSTCODE)
        page.get_by_placeholder("Your City *").fill(CITY)
        page.get_by_placeholder("Your State *").fill(STATE)
        page.locator("select").select_option(value=COUNTRY_VALUE)
        page.get_by_placeholder("Your phone *").fill(PHONE)
        page.get_by_placeholder("Your email *").fill(EMAIL)
        page.get_by_placeholder("Your password").fill(PASSWORD)

        page.get_by_role("button", name="Register").click()

        # Should redirect to login after successful registration
        page.wait_for_url("**/auth/login**", timeout=20_000)
        expect(page).to_have_url(re.compile(r"/auth/login"))

    def test_step5_login_with_new_user(self, page: Page):
        """Step 5 — Login with the newly registered credentials succeeds."""
        page.goto(f"{BASE_URL}/auth/login", wait_until="networkidle")

        page.get_by_placeholder("Your email").fill(EMAIL)
        page.get_by_placeholder("Your password").fill(PASSWORD)
        page.locator("input[type='submit']").click()

        page.wait_for_url("**/account**", timeout=20_000)
        expect(page).to_have_url(re.compile(r"/account"))
        expect(page.get_by_text(FIRST_NAME, exact=False)).to_be_visible(timeout=10_000)


# ── Standalone runner (python test_practice_registration.py) ───────────────
def _run_standalone():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=700)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page    = context.new_page()

        print(f"\n{'='*55}")
        print(f"  Name    : {FIRST_NAME} {LAST_NAME}")
        print(f"  Email   : {EMAIL}")
        print(f"  Password: {PASSWORD}")
        print(f"{'='*55}\n")

        print("[1/5] Navigating to home ...")
        page.goto(BASE_URL, wait_until="networkidle")
        print("      ✓ Home page loaded")

        print("[2/5] Clicking 'Sign in' ...")
        page.get_by_role("link", name="Sign in").click()
        page.wait_for_url("**/auth/login**")
        print("      ✓ Login page reached")

        print("[3/5] Clicking 'Register your account' ...")
        page.get_by_role("link", name="Register your account").click()
        page.wait_for_url("**/auth/register**")
        print("      ✓ Registration page reached")

        print("[4/5] Filling registration form ...")
        page.get_by_placeholder("First name *").fill(FIRST_NAME)
        page.get_by_placeholder("Your last name *").fill(LAST_NAME)
        page.get_by_placeholder("YYYY-MM-DD").fill(DOB)
        page.get_by_placeholder("Your Street *").fill(STREET)
        page.get_by_placeholder("Your Postcode *").fill(POSTCODE)
        page.get_by_placeholder("Your City *").fill(CITY)
        page.get_by_placeholder("Your State *").fill(STATE)
        page.locator("select").select_option(value=COUNTRY_VALUE)
        page.get_by_placeholder("Your phone *").fill(PHONE)
        page.get_by_placeholder("Your email *").fill(EMAIL)
        page.get_by_placeholder("Your password").fill(PASSWORD)
        page.get_by_role("button", name="Register").click()
        page.wait_for_url("**/auth/login**")
        print(f"      ✓ Registered: {FIRST_NAME} {LAST_NAME} / {EMAIL}")

        print("[5/5] Logging in ...")
        page.get_by_placeholder("Your email").fill(EMAIL)
        page.get_by_placeholder("Your password").fill(PASSWORD)
        page.locator("input[type='submit']").click()
        page.wait_for_url("**/account**")
        print(f"      ✓ Logged in as {FIRST_NAME} {LAST_NAME}")
        print(f"\n{'='*55}")
        print(f"  ALL STEPS PASSED  |  URL: {page.url}")
        print(f"{'='*55}\n")

        time.sleep(3)
        browser.close()


if __name__ == "__main__":
    _run_standalone()
