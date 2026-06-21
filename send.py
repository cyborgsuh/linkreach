import pandas as pd
import random
import time
from datetime import datetime
from browser import open_page, goto, logged_out, human_type, human_click
from config import MESSAGE_TEMPLATE

# ---------- CONFIG ----------
CSV_FILE = 'connections.csv'
LOG_FILE = 'message_log.txt'

SEND_LIMIT = 15
MIN_DELAY = 90
MAX_DELAY = 240


# ---------- LOGGING ----------
def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")


# ---------- DELAYS ----------
def jittered_sleep(base_min, base_max):
    base = random.uniform(base_min, base_max)
    jitter = random.gauss(0, base * 0.15)
    time.sleep(max(base_min * 0.5, base + jitter))


# ---------- WARM-UP ----------
def warm_up(page):
    print("Warming up session...")
    goto(page, "https://www.linkedin.com/feed/")
    page.wait_for_timeout(random.randint(4000, 8000))
    for _ in range(random.randint(2, 4)):
        page.mouse.wheel(0, random.randint(400, 900))
        page.wait_for_timeout(random.randint(1500, 3500))
    if random.random() < 0.5:
        goto(page, "https://www.linkedin.com/notifications/")
        page.wait_for_timeout(random.randint(3000, 6000))
    print("Warm-up done.")


# ---------- SEND ----------
def send_message(page, first_name, identifier, last_name):
    try:
        print(f"Opening profile for {first_name}...")
        goto(page, f"https://www.linkedin.com/in/{identifier}/")
        page.wait_for_timeout(random.randint(2000, 4000))

        link = page.locator("a[href*='/messaging/compose']").first
        if not link.count():
            log(f"No message button, skipping: {first_name} ({identifier})")
            return False
        goto(page, "https://www.linkedin.com" + link.get_attribute("href"))

        for _ in range(15):
            page.wait_for_timeout(1000)
            if page.locator("[class*='msg-s-event-listitem']").count():
                log(f"Already in thread, skipping: {first_name} {last_name} ({identifier})")
                return True

        box = page.locator("div.msg-form__contenteditable[contenteditable='true']").first
        if not box.count():
            log(f"No compose box (limit/restricted?), skipping: {first_name} ({identifier})")
            return False

        print(f"Sending message to {first_name}...")
        human_click(page, box)
        for j, line in enumerate(MESSAGE_TEMPLATE.format(first_name=first_name).split("\n")):
            if j:
                page.keyboard.press("Shift+Enter")
            human_type(page, line)

        page.wait_for_timeout(random.randint(600, 1200))
        send_btn = page.locator("button.msg-form__send-button").first
        human_click(page, send_btn)
        page.wait_for_timeout(random.randint(1200, 2000))
        log(f"Messaged: {first_name} {last_name} ({identifier})")
        return True

    except Exception as e:
        log(f"Error: {first_name} ({identifier}) — {e}")
        return False


# ---------- MAIN ----------
def main():
    print("Loading CSV...")
    df = pd.read_csv(CSV_FILE)

    if "messaged" not in df.columns:
        df["messaged"] = False

    unmessaged = df[~df["messaged"].astype(bool)]

    if len(unmessaged) == 0:
        print("No unmessaged contacts found.")
        return

    batch_size = min(SEND_LIMIT, len(unmessaged))
    batch = unmessaged.sample(batch_size).reset_index(drop=True)

    print("\n========== BATCH REVIEW ==========\n")
    for i, row in batch.iterrows():
        print(f"[{i}] {row['First Name']} ({row['identifier']})")

    print("\n-----------------------------------")
    skip_input = input(
        "Enter indices to SKIP permanently (comma separated), or press Enter to send all:\n> "
    ).strip()

    skip_indices = set()
    if skip_input:
        try:
            skip_indices = {int(x.strip()) for x in skip_input.split(",")}
        except ValueError:
            print("Invalid input. Continuing without skips.")

    approved = []
    for i, row in batch.iterrows():
        identifier = row["identifier"]
        if i in skip_indices:
            df.loc[df["identifier"] == identifier, "messaged"] = True
            print(f"Skipped permanently: {row['First Name']}")
        else:
            approved.append(row)

    df.to_csv(CSV_FILE, index=False)

    print("\n===================================")
    print(f"{len(approved)} contacts approved for sending.")
    input("Press Enter to start sending...")

    pw, ctx, page = open_page(headless=True)

    if logged_out(page):
        print("Not logged in. Run:  python login.py")
        ctx.close()
        pw.stop()
        return

    try:
        warm_up(page)

        for i, person in enumerate(approved):
            first_name = person["First Name"]
            last_name = person["Last Name"]
            identifier = person["identifier"]

            success = send_message(page, first_name, identifier, last_name)

            if logged_out(page):
                print("Logged out mid-run — stopping.")
                break

            if success:
                df.loc[df["identifier"] == identifier, "messaged"] = True
                df.to_csv(CSV_FILE, index=False)

            if i < len(approved) - 1:
                jittered_sleep(MIN_DELAY, MAX_DELAY)

        print("Batch completed.")
    finally:
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    main()
