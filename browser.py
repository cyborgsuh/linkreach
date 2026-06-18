from playwright.sync_api import sync_playwright


def open_page(profile="pw-profile", start_url="https://www.linkedin.com/feed/", headless=False):
    """Open a persistent Chromium and land on LinkedIn (login once, session is saved)."""
    pw = sync_playwright().start()
    ctx = pw.chromium.launch_persistent_context(profile, headless=headless)
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
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
