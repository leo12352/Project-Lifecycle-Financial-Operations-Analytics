"""Capture each offline dashboard page using a local Edge installation."""

from pathlib import Path
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
PAGES = ["overview", "cash", "tax", "vouchers"]

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path=str(EDGE), headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
    page.goto((ROOT / "powerbi" / "dashboard.html").as_uri())
    assert page.locator("nav button").count() == 4
    for name in PAGES:
        page.locator(f"nav button[data-page='{name}']").click()
        assert page.locator(f"section#{name}.active").count() == 1
        destination = ROOT / "powerbi" / f"dashboard_{name}.png"
        page.screenshot(path=str(destination), full_page=True)
        print(destination)
    browser.close()
