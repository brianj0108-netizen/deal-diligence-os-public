import requests
from datetime import datetime

# ==========================================
# 1. SETUP & AUTH (The Professional Way)
# ==========================================
keys = {}
try:
    with open("/home/brian/.secrets/keys.txt") as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=')
                keys[k.strip()] = v.strip()
except Exception as e:
    print(f"❌ Error loading keys file: {e}")
    exit()

token = keys.get("TELEGRAM_TOKEN")
CHAT_ID = keys.get("CHAT_ID")

if not token or not CHAT_ID:
    print("❌ Error: Missing TELEGRAM_TOKEN or CHAT_ID in keys.txt")
    exit()

# ==========================================
# 2. THE COMEBACK PROTOCOL
# ==========================================
# 0=Monday, 1=Tuesday, ... 6=Sunday
schedule = {
    0: (
        "⚔️ **MONDAY: CHEST & TRICEPS (The Entry)**\n"
        "------------------------------------\n"
        "• Flat Bench Press: 4 sets x 8 reps\n"
        "• Incline Dumbbell Press: 3 sets x 10 reps\n"
        "• Cable Flys: 3 sets x 15 reps\n"
        "• Tricep Rope Pushdowns: 4 sets x 12 reps\n"
        "• Overhead Extensions: 3 sets x 12 reps"
    ),
    1: (
        "🦍 **TUESDAY: BACK & BICEPS (The Pull)**\n"
        "------------------------------------\n"
        "• Deadlifts (or Rack Pulls): 3 sets x 5 reps\n"
        "• Lat Pulldowns (Wide Grip): 4 sets x 10 reps\n"
        "• Seated Cable Rows: 3 sets x 12 reps\n"
        "• Barbell Curls: 3 sets x 10 reps\n"
        "• Hammer Curls: 3 sets x 12 reps"
    ),
    2: (
        "🫁 **WEDNESDAY: ACTIVE RECOVERY**\n"
        "------------------------------------\n"
        "• 30 Minute Zone 2 Cardio (Jog/Incline Walk)\n"
        "• 15 Minute Deep Stretch / Mobility\n"
        "• Core: Planks (3 sets x 60s)"
    ),
    3: (
        "🦵 **THURSDAY: LEGS (The Foundation)**\n"
        "------------------------------------\n"
        "• Squats: 4 sets x 6-8 reps\n"
        "• Leg Press: 3 sets x 12 reps\n"
        "• Romanian Deadlifts: 3 sets x 10 reps\n"
        "• Calf Raises: 4 sets x 15 reps"
    ),
    4: (
        "🛡️ **FRIDAY: UPPER BODY PUMP (The Armor)**\n"
        "------------------------------------\n"
        "• Overhead Press (Standing): 4 sets x 8 reps\n"
        "• Lateral Raises (Dumbbell): 4 sets x 15 reps\n"
        "• Face Pulls: 4 sets x 15 reps\n"
        "• Chin-ups: 3 sets x AMRAP (As Many As Possible)\n"
        "• Bicep/Tricep Superset: 3 sets x 12 reps"
    ),
    5: (
        "🏔️ **SATURDAY: THE WILD CARD**\n"
        "------------------------------------\n"
        "• 1 Hour Activity: Hike, Sport, or Long Ruck.\n"
        "• Get out of the house. No screens."
    ),
    6: (
        "🥩 **SUNDAY: STRATEGY & PREP**\n"
        "------------------------------------\n"
        "• Meal Prep for the week.\n"
        "• Review Chase calendar.\n"
        "• Sleep 8+ hours."
    )
}

# ==========================================
# 3. THE TRANSMISSION
# ==========================================
def send_workout():
    day_index = datetime.now().weekday()
    workout = schedule.get(day_index, "Rest Day")
    
    # The Header that sets the tone
    message = f"🔥 **THE COMEBACK** 🔥\n\n{workout}\n\n*Log this in your RPG when done.*"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": CHAT_ID, 
        "text": message, 
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ Mission transmitted.")
        else:
            print(f"❌ Transmission failed: {response.text}")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    send_workout()
