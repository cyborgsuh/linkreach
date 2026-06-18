import os
import re
import pandas as pd
import sys
from browser import open_page, goto, logged_out

CSV_FILE = "Connections.csv"
URL = "https://www.linkedin.com/mynetwork/invite-connect/connections/"

pw, ctx, page = open_page(start_url=URL, headless=os.environ.get("HEADLESS") == "1")

if logged_out(page):
    print("Not logged in. Run:  python login.py", flush=True)
    ctx.close()
    pw.stop()
    sys.exit(1)
page.wait_for_timeout(5000)

# Read the target count from the page header ("2,663 connections").
total = 0
m = re.search(r"([\d,]+)\s+connections", page.inner_text("body"), re.I)
if m:
    total = int(m.group(1).replace(",", ""))
print(f"Target: {total or '?'} connections", flush=True)

# The list is virtualized: off-screen cards leave the DOM, so harvest while scrolling.
people = {}
prev, stable, i = 0, 0, 0
while i < 2000:
    i += 1
    data = page.eval_on_selector_all(
        "main a[href*='/in/']",
        "els => els.map(e => ({href: e.href, name: e.innerText, aria: e.getAttribute('aria-label') || ''}))",
    )
    for d in data:
        mm = re.search(r"/in/([^/?]+)", d["href"])
        if not mm:
            continue
        slug = mm.group(1)
        name = (d["name"] or "").strip().split("\n")[0].strip()
        if not name and d["aria"]:  # avatar link has no text; name is in its aria-label
            name = re.sub(r"[’']s profile picture$", "", d["aria"]).strip()
        if slug not in people or (name and not people[slug]):
            people[slug] = name

    page.eval_on_selector_all(
        "main a[href*='/in/']",
        "els => { if (els.length) els[els.length - 1].scrollIntoView({block: 'end'}); }",
    )
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(900)

    n = len(people)
    print(f"iter {i}: {n}/{total or '?'}", flush=True)
    if total and n >= total - 3:          # got essentially everyone
        break
    if n == prev:
        stable += 1
    else:
        prev, stable = n, 0
    if stable >= 15:                       # plateaued (LinkedIn stopped loading) -> stop
        print("Plateaued — stopping.", flush=True)
        break

ctx.close()
pw.stop()

rows = []
for slug, name in people.items():
    parts = name.split(" ", 1) if name else [slug]
    rows.append({
        "First Name": parts[0],
        "Last Name": parts[1] if len(parts) > 1 else "",
        "URL": f"https://www.linkedin.com/in/{slug}",
        "identitfier": slug,
        "messaged": False,
    })

new = pd.DataFrame(rows)
old = pd.read_csv(CSV_FILE)
# keep="first" preserves existing rows AND their messaged status; new uniques append as False.
merged = pd.concat([old, new]).drop_duplicates(subset="identitfier", keep="first")
merged.to_csv(CSV_FILE, index=False)
print(f"Scraped {len(new)} | total {len(merged)} | added {len(merged) - len(old)} new.", flush=True)
