"""
titan_trainer.py

Simple Telegram workout scheduler.

- Reads Telegram credentials from config_public.py
- Looks up today's workout in WORKOUT_PLANS
- Sends it to your Telegram chat

You can customize the workouts by editing the WORKOUT_PLANS
dictionary below. No Python knowledge required if you only
change the text inside the triple quotes.
"""

from datetime import datetime
import requests
from config_public import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

# ================================
# EDIT THIS SECTION ONLY
# Customize your workout plan here
# ================================

# Keys: lowercase weekday names ("monday", "tuesday", ...)
# Values: the message that will be sent to you on that day.
WORKOUT_PLANS = {
    "monday": """Upper Body A:
- Bench Press 3x8
- Barbell Row 3x10
- Shoulder Press 3x10
- Planks 3x30s""",

    "wednesday": """Lower Body:
- Squats 3x8
- Romanian Deadlift 3x10
- Lunges 3x10/leg
- Hanging Leg Raises 3x10""",

    "friday": """Upper Body B:
- Incline DB Press 3x8
- Pull-ups 3xAMRAP
- Dips 3xAMRAP
- Side Planks 3x30s/side""",
}

# If you want workouts on other days, add entries like:
# "tuesday": "Your cardio / conditioning plan here",


# ================================
# BELOW THIS LINE: LOGIC
# You normally do NOT need to edit
# ================================

def send_telegram_message(text: str) -> None:
    """Send a plain-text message to your Telegram chat."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID in keys.local.txt")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            print(f"❌ Telegram error: {resp.status_code} {resp.text}")
        else:
            print("✅ Workout message sent to Telegram")
    except Exception as e:
        print(f"⚠️ Telegram send error: {e}")


def get_today_key() -> str:
    """Return today's weekday name in lowercase (e.g. 'monday')."""
    return datetime.now().strftime("%A").lower()


def main():
    today = get_today_key()
    print(f"📅 Today is: {today}")

    workout = WORKOUT_PLANS.get(today)

    if not workout:
        print("ℹ️ No workout scheduled for today in WORKOUT_PLANS.")
        return

    message = f"💪 *Today's Workout* ({today.title()}):\n\n{workout}"
    send_telegram_message(message)


if __name__ == "__main__":
    main()
