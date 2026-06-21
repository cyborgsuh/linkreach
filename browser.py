import json
import random
import time
from playwright.sync_api import sync_playwright

try:
    from playwright_stealth import Stealth
    _stealth = Stealth()
    _STEALTH_AVAILABLE = True
except ImportError:
    _STEALTH_AVAILABLE = False


def open_page(cookies_path="cookies.json", profile="pw-profile", start_url="https://www.linkedin.com/feed/", headless=False):
    """Launch Chrome using cookies.json if present, else fall back to pw-profile/."""
    import os
    pw = sync_playwright().start()

    if os.path.exists(cookies_path):
        print(f"Auth: using {cookies_path}")
        with open(cookies_path) as f:
            raw = json.load(f)
        cookie_names = ["li_at", "JSESSIONID", "lidc", "bcookie", "bscookie"]
        cookies = [
            {"name": k, "value": v, "domain": ".linkedin.com", "path": "/"}
            for k, v in raw.items()
            if k in cookie_names
        ]
        browser = pw.chromium.launch(
            channel="chrome",
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context()
        ctx.add_cookies(cookies)
        page = ctx.new_page()

    elif os.path.exists(profile):
        print(f"Auth: using {profile}/")
        ctx = pw.chromium.launch_persistent_context(
            profile,
            channel="chrome",
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

    else:
        pw.stop()
        raise FileNotFoundError("No auth found. Run  python login.py  for setup instructions.")

    if _STEALTH_AVAILABLE:
        _stealth.apply_stealth_sync(page)
    goto(page, start_url)
    return pw, ctx, page


def goto(page, url, tries=3):
    """Navigate, tolerating LinkedIn's SPA redirects that can interrupt a load."""
    for i in range(tries):
        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            return
        except Exception:
            page.wait_for_timeout(2000)


def logged_out(page):
    """True if LinkedIn bounced us to a login/auth page (session expired)."""
    return any(x in page.url for x in ("/login", "/authwall", "/uas/", "/checkpoint"))


def human_type(page, text):
    """Type text character-by-character with variable per-key delays."""
    for ch in text:
        page.keyboard.type(ch)
        page.wait_for_timeout(random.randint(40, 160))
        if random.random() < 0.04:
            time.sleep(random.uniform(0.3, 0.9))


def human_click(page, element):
    """Move mouse near element centre with slight randomness before clicking."""
    box = element.bounding_box()
    if box:
        page.mouse.move(
            box["x"] + box["width"] / 2 + random.uniform(-5, 5),
            box["y"] + box["height"] / 2 + random.uniform(-3, 3),
        )
        page.wait_for_timeout(random.randint(100, 400))
    element.click()
