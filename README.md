# linkedin-connector

A lightweight CLI toolkit to scrape your LinkedIn connections and send personalised outreach messages at a human pace, with built-in deduplication, cooldowns, and session persistence.

> **Disclaimer:** Use responsibly and in accordance with [LinkedIn's User Agreement](https://www.linkedin.com/legal/user-agreement). Automated messaging may violate their ToS. This tool is for personal, educational use only.

---

## What it does

| Script | Purpose |
|---|---|
| `login.py` | Open a browser, log into LinkedIn once, save the session |
| `scrape.py` | Scroll through your connections page and export them to `Connections.csv` |
| `mark_replied.py` | Scroll your inbox and mark everyone you've already messaged |
| `send.py` | Send a personalised message to a batch of unmessaged connections |

---

## Prerequisites

- Python 3.9+
- A LinkedIn account

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/cyborgsuh/linkedin-connector.git
cd linkedin-connector
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Create your config

```bash
cp config.example.py config.py
```

Edit `config.py` and fill in your name, role, and message. This file is gitignored so it stays local.

### 4. Log in once

```bash
python login.py
```

A browser window opens. Log into LinkedIn manually, then press **Enter** in the terminal. Your session is saved to `pw-profile/` and reused by all other scripts. You only need to do this once (or after your session expires).

---

## Usage

### Step 1: Scrape your connections

```bash
python scrape.py
```

Scrolls your LinkedIn connections page and writes/merges results into `Connections.csv`. Existing rows (and their `messaged` status) are preserved.

### Step 2: (Optional) Mark already-messaged contacts

```bash
python mark_replied.py
```

Scrolls your LinkedIn inbox and marks any connections you've already messaged as `messaged=True` in the CSV. Run this before `send.py` to avoid double-messaging people.

### Step 3: Send messages

```bash
python send.py
```

Picks a random batch of unmessaged contacts, shows them for review, lets you skip specific entries, then sends messages one by one with a random cooldown between each.

---

## Configuration

All config is at the top of `send.py`:

```python
CSV_FILE    = 'connections.csv'   # path to your connections CSV
LOG_FILE    = 'message_log.txt'   # where sent messages are logged
SEND_LIMIT  = 10                  # max messages per run
MIN_DELAY   = 60                  # seconds, minimum wait between messages
MAX_DELAY   = 160                 # seconds, maximum wait between messages
```

### Customise the message template

Edit `MESSAGE_TEMPLATE` in `config.py`. Use `{first_name}` as the only placeholder:

```python
MESSAGE_TEMPLATE = """Hey {first_name},

I'm [YOUR NAME] at [YOUR COMPANY]. ...
"""
```

---

## CSV format

`Connections.csv` is created automatically by `scrape.py`. If you want to start from LinkedIn's own export ([download here](https://www.linkedin.com/mypreferences/d/download-my-data)), make sure it has at least these columns:

| Column | Description |
|---|---|
| `First Name` | Contact's first name |
| `Last Name` | Contact's last name |
| `URL` | Full LinkedIn profile URL |
| `identifier` | LinkedIn slug (the part after `/in/`) |
| `messaged` | `True` / `False`, set automatically |

---

## Files excluded from git

The following are in `.gitignore` and will never be committed:

- `*.csv` — contains personal contact data
- `message_log.txt` — contains names and timestamps
- `pw-profile/` — contains your LinkedIn session cookies
- `config.py` — contains your personal message template

---

## Contributing

Contributions are welcome. To get started:

1. Fork the repo
2. Create a branch: `git checkout -b your-feature`
3. Make your changes and commit: `git commit -m "add your feature"`
4. Push and open a PR against `master`

Please keep PRs focused on a single change. If you're planning something big, open an issue first to discuss it.

---

## License

MIT
