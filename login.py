from browser import open_page

# Opens a visible browser so you can log into LinkedIn once; the session is saved to pw-profile/
# and reused by scrape.py / mark_replied.py / send.py.
pw, ctx, page = open_page(start_url="https://www.linkedin.com/login", headless=False)
input("Log into LinkedIn in the browser window, then press Enter here to save the session...")
ctx.close()
pw.stop()
print("Session saved. You can now run scrape.py / mark_replied.py / send.py.")
