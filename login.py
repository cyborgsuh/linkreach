import json
import subprocess
import sys
import time
import requests

# ---------- CONFIG ----------
# Switch between login methods:
#   "browser"  — opens Chrome via Playwright, auto-saves cookies.json after login
#   "manual"   — prints DevTools instructions, you fill cookies.json yourself
LOGIN_METHOD = "browser"


# ---------- BROWSER LOGIN (Playwright) ----------
def browser_login():
    import websocket
    CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    DEBUG_PORT = 9222
    import os
    PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome-debug-profile")

    def kill_chrome():
        subprocess.call(["taskkill", "/F", "/IM", "chrome.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)

    kill_chrome()
    subprocess.Popen([
        CHROME,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        "https://www.linkedin.com/login",
    ])

    print("Waiting for Chrome", end="", flush=True)
    for _ in range(30):
        try:
            requests.get(f"http://localhost:{DEBUG_PORT}/json", timeout=1)
            print(" ready.")
            break
        except Exception:
            print(".", end="", flush=True)
            time.sleep(1)
    else:
        print("\nERROR: Chrome debug port never opened.")
        sys.exit(1)

    input("\nLog in to LinkedIn in the Chrome window, then press Enter...\n")

    r = requests.get(f"http://localhost:{DEBUG_PORT}/json", timeout=5)
    tabs = r.json()
    ws_url = next((t["webSocketDebuggerUrl"] for t in tabs if t.get("type") == "page"), None)
    if not ws_url:
        print("ERROR: No debuggable tab found.")
        sys.exit(1)

    ws = websocket.create_connection(ws_url, timeout=10)
    ws.send(json.dumps({"id": 1, "method": "Network.getAllCookies"}))
    result = json.loads(ws.recv())
    ws.close()

    cookies = {c["name"]: c["value"] for c in result["result"]["cookies"]}
    li_at = cookies.get("li_at")
    jsessionid = cookies.get("JSESSIONID")

    if not li_at or not jsessionid:
        print("ERROR: Cookies not found — make sure login completed before pressing Enter.")
        sys.exit(1)

    out = {"li_at": li_at, "JSESSIONID": jsessionid}
    for name in ["lidc", "bcookie", "bscookie"]:
        if name in cookies:
            out[name] = cookies[name]

    with open("cookies.json", "w") as f:
        json.dump(out, f, indent=2)

    print("cookies.json saved. Run send.py to start messaging.")


# ---------- MANUAL LOGIN ----------
def manual_login():
    print("""
========== LinkedIn Session Setup ==========

1. Open Chrome and go to: https://www.linkedin.com
2. Log in (complete any CAPTCHA if shown)
3. Press F12 -> Application -> Cookies -> https://www.linkedin.com
4. Copy values for these cookies into cookies.json:

   Required:
     li_at        (long string starting with AQED...)
     JSESSIONID   (looks like  ajax:1234567890123456)

   Optional (helps avoid redirects):
     lidc / bcookie / bscookie

5. cookies.json format:

   {
     "li_at": "paste here",
     "JSESSIONID": "paste here",
     "lidc": "paste here",
     "bcookie": "paste here",
     "bscookie": "paste here"
   }

6. Run send.py.

=============================================
""")


# ---------- MAIN ----------
if __name__ == "__main__":
    if LOGIN_METHOD == "browser":
        browser_login()
    else:
        manual_login()
