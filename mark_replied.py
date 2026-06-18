import os
import re
import sys
import pandas as pd
from browser import open_page, goto, logged_out

CSV_FILE = "Connections.csv"
INBOX = "https://www.linkedin.com/messaging/"


def norm(s):
    """Lowercase, drop punctuation/emoji/zero-width, collapse spaces — for name matching."""
    s = re.sub(r"[^\w\s]", "", str(s), flags=re.UNICODE)
    return re.sub(r"\s+", " ", s).strip().lower()


pw, ctx, page = open_page(start_url=INBOX, headless=os.environ.get("HEADLESS") == "1")

if logged_out(page):
    print("Not logged in. Run:  python login.py", flush=True)
    ctx.close()
    pw.stop()
    sys.exit(1)
page.wait_for_timeout(6000)

# Conversation list is virtualized; harvest participant names (first line of each card) while scrolling.
names = set()
prev, stable, i = 0, 0, 0
while i < 800:
    i += 1
    texts = page.eval_on_selector_all(
        "[class*='msg-conversation-card']", "els => els.map(e => e.innerText)"
    )
    for t in texts:
        first = (t or "").strip().split("\n")[0].strip()
        if first:
            names.add(norm(first))
    page.eval_on_selector_all(
        "[class*='msg-conversation-card']",
        "els => { if (els.length) els[els.length - 1].scrollIntoView({block: 'end'}); }",
    )
    page.wait_for_timeout(1200)
    n = len(names)
    print(f"inbox scroll {i}: {n} unique names", flush=True)
    if n == prev:
        stable += 1
    else:
        prev, stable = n, 0
    if stable >= 30:  # be very patient — transient stalls shouldn't end the scroll early
        break

ctx.close()
pw.stop()

df = pd.read_csv(CSV_FILE)
if "messaged" not in df.columns:
    df["messaged"] = False
df["_full"] = (df["First Name"].fillna("") + " " + df["Last Name"].fillna("")).map(norm)

marked = 0
for name in names:
    hits = df.index[(df["_full"] == name) & (df["messaged"] != True)]
    if len(hits) == 1:  # only mark unambiguous (single) name matches
        df.loc[hits, "messaged"] = True
        marked += 1

df = df.drop(columns="_full")
df.to_csv(CSV_FILE, index=False)
print(f"Inbox names: {len(names)} | newly marked messaged=True: {marked}", flush=True)
print("(Ambiguous duplicate names are left for the send-time auto-detect to catch.)", flush=True)
