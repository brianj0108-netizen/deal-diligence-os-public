import sys
from pathlib import Path

# Base directory of this project (where keys.local.txt should live)
BASE_DIR = Path(__file__).resolve().parent.parent
KEYS_FILE = BASE_DIR / "keys.local.txt"

keys = {}

try:
    with open(KEYS_FILE) as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                keys[k.strip().upper()] = v.strip()
except FileNotFoundError:
    print(f"❌ keys.local.txt not found at {KEYS_FILE}")
    print("   -> Copy keys.example.txt to keys.local.txt and fill in your own values.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error loading keys from {KEYS_FILE}: {e}")
    sys.exit(1)

# Exposed config values (names match what the bot expects)
TELEGRAM_TOKEN       = keys.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID     = keys.get("TELEGRAM_CHAT_ID")

NOTION_KEY           = keys.get("NOTION_KEY")
RPG_DATABASE_ID      = keys.get("RPG_DATABASE_ID")
JOURNAL_DATABASE_ID  = keys.get("JOURNAL_DATABASE_ID")
PAYCHECK_DATABASE_ID = keys.get("PAYCHECK_DATABASE_ID")

PERPLEXITY_KEY       = keys.get("PERPLEXITY_KEY")

EMAIL_SENDER         = keys.get("EMAIL_SENDER")
EMAIL_PASSWORD       = keys.get("EMAIL_PASSWORD")
EMAIL_RECEIVER       = keys.get("EMAIL_RECEIVER")
