import pandas as pd
import random
import time
from datetime import datetime
from browser import open_page, goto, logged_out
from config import MESSAGE_TEMPLATE

# ---------- CONFIG ----------
CSV_FILE = ‘connections.csv’
LOG_FILE = ‘message_log.txt’

SEND_LIMIT = 10
MIN_DELAY = 60
MAX_DELAY = 160

# ---------- LOGGING ----------
def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")


# ---------- SEND FUNCTION ----------
def send_message(page, first_name, identifier, last_name):
    try:
        print(f"Opening profile for {first_name}...")
        goto(page, f"https://www.linkedin.com/in/{identifier}/")
        page.wait_for_timeout(random.randint(2000, 4000))

        # The "Message" button is an <a> to the compose page; navigate to it directly
        # (clicking it is blocked by an overlay element).
        link = page.locator("a[href*='/messaging/compose']").first
        if not link.count():
            log(f"No message button, skipping: {first_name} ({identifier})")
            return False
        goto(page, "https://www.linkedin.com" + link.get_attribute("href"))

        # Message history loads a few seconds AFTER the compose page opens, so poll for it.
        # Checking once too early misses existing threads and re-messages people.
        for _ in range(15):
            page.wait_for_timeout(1000)
            if page.locator("[class*='msg-s-event-listitem']").count():
                log(f"Already in thread, skipping: {first_name} {last_name} ({identifier})")
                return True

        # No compose box -> restricted / rate-limited.
        box = page.locator("div.msg-form__contenteditable[contenteditable='true']").first
        if not box.count():
            log(f"No compose box (limit/restricted?), skipping: {first_name} ({identifier})")
            return False

        print(f"Sending message to {first_name}...")
        box.click()
        for j, line in enumerate(MESSAGE_TEMPLATE.format(first_name=first_name).split("\n")):
            if j:
                page.keyboard.press("Shift+Enter")  # newline without sending
            page.keyboard.type(line)

        page.wait_for_timeout(800)
        page.locator("button.msg-form__send-button").first.click()
        page.wait_for_timeout(1500)
        log(f"Messaged: {first_name} {last_name} ({identifier})")
        return True

    except Exception as e:
        print(f"Error details: {e}")
        return False


# ---------- MAIN ----------
def main():
    print("Loading CSV...")

    df = pd.read_csv(CSV_FILE)

    if "messaged" not in df.columns:
        df["messaged"] = False

    unmessaged = df[df["messaged"] == False]

    if len(unmessaged) == 0:
        print("No unmessaged contacts found.")
        return

    batch_size = min(SEND_LIMIT, len(unmessaged))
    batch = unmessaged.sample(batch_size).reset_index(drop=True)

    print("\n========== BATCH REVIEW ==========\n")

    for i, row in batch.iterrows():
        print(f"[{i}] {row['First Name']} ({row['identitfier']})")

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
        identifier = row["identitfier"]

        if i in skip_indices:
            df.loc[df["identitfier"] == identifier, "messaged"] = True
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
        # ---------- SEND LOOP ----------
        for person in approved:
            first_name = person["First Name"]
            last_name = person["Last Name"]
            identifier = person["identitfier"]

            success = send_message(page, first_name, identifier, last_name)

            if logged_out(page):
                print("Logged out of LinkedIn mid-run — stopping. Run python login.py, then re-run.")
                break

            if success:
                df.loc[df["identitfier"] == identifier, "messaged"] = True
                df.to_csv(CSV_FILE, index=False)

            delay = random.randint(MIN_DELAY, MAX_DELAY)
            print(f"Cooldown: {delay}s before next message")
            if batch_size > 1:
                time.sleep(delay)
            else:
                print("Single message sent, skipping cooldown.")
        print("Batch completed.")
    finally:
        ctx.close()
        pw.stop()


if __name__ == "__main__":
    main()