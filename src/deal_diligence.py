import smtplib, ssl, traceback, re, sys, json, os
import yfinance as yf
import requests
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import pytz
from openai import OpenAI

# ==========================================
# 1. CONFIGURATION & SECRETS
# ==========================================
keys = {}
try:
    with open("/home/brian/.secrets/keys.txt") as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                keys[k.strip().upper()] = v.strip()
except FileNotFoundError:
    print("❌ Error: Keys file not found.")
    sys.exit(1)

client = OpenAI(api_key=keys.get("PERPLEXITY_KEY"), base_url="https://api.perplexity.ai")
SENDER_EMAIL = keys.get("SENDER_EMAIL")
SENDER_PASSWORD = keys.get("SENDER_PASSWORD")
RECEIVER_EMAIL = keys.get("RECEIVER_EMAIL") or "BrianJ0108@gmail.com"
FINNHUB_KEY = keys.get("FINNHUB_KEY")

LOG_FILE = "/home/brian/deal_diligence.log"
HISTORY_FILE = "/home/brian/market_history.json"

# ==========================================
# 2. LOGGING SYSTEM
# ==========================================
def log_event(message):
    """Append timestamped events to log file for debugging."""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"⚠️ Logging failed: {e}")

# ==========================================
# 3. HISTORICAL DATA TRACKER
# ==========================================
def save_market_snapshot(data, day_type):
    """Save today's market data for future reference."""
    try:
        history = load_market_history()
        today = datetime.now().strftime('%Y-%m-%d')

        history[today] = {
            "day_type": day_type,
            "data": {k: v for k, v in data.items()},
            "timestamp": datetime.now().isoformat()
        }

        sorted_dates = sorted(history.keys(), reverse=True)
        history = {k: history[k] for k in sorted_dates[:30]}

        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)

        log_event(f"📊 Saved market snapshot for {today}")
    except Exception as e:
        log_event(f"⚠️ Failed to save history: {e}")

def load_market_history():
    """Load historical market data."""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def get_week_performance(data):
    """Calculate week-over-week performance."""
    try:
        tickers = {
            "S&P 500": data["S&P 500"]["ticker"],
            "Nasdaq 100": data["Nasdaq 100"]["ticker"],
            "Bitcoin": "BTC-USD"
        }

        weekly_perf = {}
        for name, ticker in tickers.items():
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")

            if len(hist) >= 5:
                week_ago = hist['Close'].iloc[-6] if len(hist) > 5 else hist['Close'].iloc[0]
                current = hist['Close'].iloc[-1]
                week_change = ((current - week_ago) / week_ago) * 100

                sign = "+" if week_change >= 0 else ""
                weekly_perf[name] = f"{sign}{week_change:.2f}%"
            else:
                weekly_perf[name] = "N/A"

        return weekly_perf
    except Exception as e:
        log_event(f"❌ Error calculating weekly performance: {e}")
        return {}

# ==========================================
# 4. FINNHUB NEWS FETCHER
# ==========================================
def get_real_news():
    """Fetch actual market news with summaries from Finnhub API."""
    if not FINNHUB_KEY:
        log_event("⚠️ FINNHUB_KEY missing - skipping news fetch")
        return "No news API key configured."
    
    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            log_event(f"⚠️ Finnhub API error: {response.status_code}")
            return "News API temporarily unavailable."
        
        news_data = response.json()
        
        now = datetime.now()
        cutoff = (now - timedelta(hours=48)).timestamp()
        
        recent_news = [
            item for item in news_data 
            if item.get('datetime', 0) > cutoff
        ][:8]
        
        if not recent_news:
            log_event("⚠️ No recent news found from Finnhub")
            return "No major market news in the past 24 hours."
        
        news_items = []
        for item in recent_news:
            headline = item.get('headline', 'N/A')
            summary = item.get('summary', '')
            source = item.get('source', 'Unknown')
            timestamp = datetime.fromtimestamp(item.get('datetime', 0)).strftime('%b %d, %I:%M %p')
            
            news_block = f"**{headline}** ({source}, {timestamp})"
            if summary:
                news_block += f"\n   Summary: {summary[:300]}"
            
            news_items.append(news_block)
        
        news_text = "\n\n".join(news_items)
        log_event(f"✅ Fetched {len(recent_news)} news items with summaries from Finnhub")
        
        return news_text
        
    except Exception as e:
        log_event(f"❌ Finnhub fetch failed: {e}")
        return f"News fetch error: {e}"

# ==========================================
# 5. DATA PIPELINE (Yahoo Finance)
# ==========================================
def get_market_data():
    print("📡 PIPELINE: Fetching verified market data...")
    log_event("📡 Starting market data fetch")

    try:
        tz_ny = pytz.timezone('America/New_York')
    except pytz.UnknownTimeZoneError:
        tz_ny = pytz.utc

    now = datetime.now(tz_ny)

    is_weekday = now.weekday() < 5
    is_market_hours = (9 <= now.hour < 16) or (now.hour == 9 and now.minute >= 30)
    market_open = is_weekday and is_market_hours

    tickers = {
        "S&P 500": "^GSPC" if market_open else "ES=F",
        "Nasdaq 100": "^NDX" if market_open else "NQ=F",
        "10-Year Yield": "^TNX",
        "WTI Crude": "CL=F",
        "Bitcoin": "BTC-USD",
        "Gold": "GC=F"
    }

    data = {}

    for name, ticker in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")

            if hist.empty:
                log_event(f"⚠️ No data returned for {name} ({ticker})")
                data[name] = {"price": 0, "change": 0, "str": "N/A", "ticker": ticker}
                continue

            last_update = hist.index[-1]
            if last_update.tzinfo is None:
                last_update = last_update.tz_localize('UTC')
            last_update_ny = last_update.astimezone(tz_ny)
            data_age_hours = (now - last_update_ny).total_seconds() / 3600
            if data_age_hours > 24:
                log_event(f"⚠️ {name} data is {data_age_hours:.1f} hours old")

            if now.weekday() == 0 and now.hour < 16:
                completed_days = hist[hist.index < now.replace(hour=0, minute=0)]
                if len(completed_days) >= 2:
                    current = completed_days['Close'].iloc[-1]
                    prev_close = completed_days['Close'].iloc[-2]
                    log_event(f"📅 Monday morning: Using Friday close for {name}: {current:.2f}")
                else:
                    current = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else hist['Open'].iloc[-1]
            else:
                current = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else hist['Open'].iloc[-1]

            if "Yield" in name:
                if current > 20:
                    current = current / 10
                    prev_close = prev_close / 10

                change_bps = (current - prev_close) * 100
                sign = "+" if change_bps >= 0 else ""
                fmt_str = f"{current:.3f}% ({sign}{change_bps:.1f} bps)"
                change_val = change_bps
            else:
                change_pct = ((current - prev_close) / prev_close) * 100
                sign = "+" if change_pct >= 0 else ""
                fmt_str = f"{current:,.2f} ({sign}{change_pct:.2f}%)"
                change_val = change_pct

            data[name] = {"price": current, "change": change_val, "str": fmt_str, "ticker": ticker}
            log_event(f"✅ Fetched {name}: {fmt_str}")

        except Exception as e:
            print(f"❌ Error fetching {name}: {e}")
            log_event(f"❌ Error fetching {name}: {e}")
            data[name] = {"price": 0, "change": 0, "str": "Error", "ticker": ticker}

    return data

# ==========================================
# 6. VALIDATION SYSTEM
# ==========================================
def validate_data(data):
    """Prevents sending garbage data."""
    sp500 = data.get("S&P 500", {}).get("price", 0)

    if sp500 == 0:
        return False, "🚨 ABORT: S&P 500 price is missing or zero."

    SP_MIN = 4500
    SP_MAX = 8500

    if not (SP_MIN < sp500 < SP_MAX):
        return False, f"🚨 ABORT: S&P 500 Price {sp500:,.2f} is outside realistic range ({SP_MIN}-{SP_MAX})."

    critical_assets = ["S&P 500", "Nasdaq 100", "10-Year Yield"]
    for asset in critical_assets:
        if data.get(asset, {}).get("str") in ["N/A", "Error"]:
            return False, f"🚨 ABORT: Missing critical data for {asset}."

    log_event(f"✅ Validation passed: S&P at {sp500:,.2f}")
    return True, ""

# ==========================================
# 7. DAY DETECTION
# ==========================================
def get_newsletter_type():
    """Determine newsletter type based on day of week."""
    now = datetime.now(pytz.timezone('America/New_York'))
    day_of_week = now.weekday()

    day_types = {
        0: "MONDAY",
        1: "WEEKDAY",
        2: "WEEKDAY",
        3: "WEEKDAY",
        4: "FRIDAY",
        5: "WEEKEND",
        6: "SUNDAY"
    }

    return day_types.get(day_of_week, "WEEKDAY")

# ==========================================
# 8. LOGIC ENGINE
# ==========================================
def get_logic_constraints(data, newsletter_type):
    sp_chg = data["S&P 500"]["change"]
    nas_chg = data["Nasdaq 100"]["change"]
    oil_chg = data["WTI Crude"]["change"]

    constraints = []

    if newsletter_type == "MONDAY":
        constraints.append("MONDAY CONTEXT: Reference Friday's close. Set up the WEEK ahead.")
    elif newsletter_type == "FRIDAY":
        constraints.append("FRIDAY CONTEXT: Summarize the week. Weekend preview.")
    elif newsletter_type == "SUNDAY":
        constraints.append("SUNDAY DEEP DIVE: Weekly recap + week ahead.")

    if sp_chg > 0.1 or nas_chg > 0.1:
        constraints.append("MARKET MOOD: Stocks bouncing. Don't oversell it.")
    elif sp_chg < -1.0:
        constraints.append("MARKET MOOD: Selling pressure. Stay factual.")

    if abs(oil_chg) > 2.0:
        constraints.append(f"OIL ALERT: WTI moving {oil_chg:.2f}%. Explain why.")

    return "\n".join(constraints)

# ==========================================
# 9. THE AI WRITER (HUMAN VOICE)
# ==========================================
def generate_content(data, newsletter_type):
    data_text = "\n".join([f"{k}: {v['str']}" for k, v in data.items()])
    logic_instructions = get_logic_constraints(data, newsletter_type)

    print(f"🧠 NEWSLETTER TYPE: {newsletter_type}")
    log_event(f"🧠 Generating {newsletter_type} newsletter")

    real_news = get_real_news()
    print(f"📰 Real news headlines:\n{real_news[:300]}...")

    weekly_perf = ""
    if newsletter_type in ["SUNDAY", "MONDAY", "FRIDAY"]:
        weekly_data = get_week_performance(data)
        if weekly_data:
            weekly_perf = f"\nWEEKLY PERFORMANCE:\n" + "\n".join([f"{k}: {v}" for k, v in weekly_data.items()])

    tz_ny = pytz.timezone('America/New_York')
    now_ny = datetime.now(tz_ny)
    today_date = now_ny.strftime('%A, %B %d, %Y')
    yesterday = (now_ny - timedelta(days=1)).strftime('%A, %B %d, %Y')
    current_time_et = now_ny.strftime('%I:%M %p ET')

    system_prompt = f"""
    You are writing a market brief for a friend who trades. It's {today_date}, {current_time_et}.

    NEWS SOURCES (use these as your factual base):
    {real_news}

    WRITING RULES:
    1. Write like a human. No em-dashes. No "tale of two markets." No poetic bullshit.
    2. Short sentences. Active voice. Get to the point.
    3. CRITICAL: ALL FACTS must come from the news sources above. If a company isn't mentioned in those sources, DO NOT write about it.
    4. If you don't have a detail, SKIP IT. Do not guess percentages, revenue numbers, or stock moves.
    5. If the news is thin, say so: "Quiet session ahead of earnings" or "No major catalysts overnight."
    6. Sound confident but not cocky. You're explaining what happened and what it means.
    7. NO AI CLICHES: No "navigate," "landscape," "ecosystem," "robust," "leverage," "delve," "underscores."
    8. Write like you're texting this to someone. Clear, direct, useful.
    9. DO NOT USE BRACKETS FOR CITATIONS: [1], [2], etc.
    10. IF A COMPANY ISN'T IN THE NEWS SOURCES ABOVE, DO NOT MENTION IT. Period.
    
    Bad: "Palantir crushed earnings with revenue of 7.2 billion." (Not in news sources = don't write it)
    Good: "Microsoft warned about AI spending, according to CNBC." (In news sources = OK to use)
    
    Bad: "Markets are navigating a complex landscape as investors digest earnings."
    Good: "Stocks fell after Microsoft warned about AI spending. Investors are nervous."
    
    Bad: "The session underscored the market's resilience amid volatility."
    Good: "Despite the selloff, the S&P held above 6,800."

    """

    if newsletter_type == "WEEKDAY":
        user_prompt = f"""
        Write the morning market brief. Use the news sources to explain what happened yesterday and what's moving today.

        MARKET DATA:
        {data_text}

        CONTEXT:
        {logic_instructions}

        STRUCTURE:
        1. LEAD (50 words max): What happened yesterday? Use ONLY events from the news sources.
        2. THE STORY (150-200 words): Explain why markets moved. Connect dots between news events.
        3. WHAT ELSE IS MOVING (150-200 words): Pick 2-3 stories from the news. Add context and why they matter.
        4. ZOOM OUT (100 words): Bigger picture - what's the trend or theme this week?
        5. BOTTOM LINE (50 words): One thing to watch today.

        Write like Morning Brew: casual, conversational, but tight and fact-driven. 
        Aim for 600-800 words total. Use headers and short paragraphs.
        But ONLY use facts from the news sources above. 
        If the news is thin, keep it short - don't pad with speculation.


        HTML TEMPLATE:
        <h3><b>☕ THE MORNING POUR</b></h3>
        <p>[Lead paragraph]</p>
        <br>
        <h3><b>📊 MARKET DASHBOARD</b></h3>
        <p><i>(Pre-Market as of {current_time_et})</i></p>
        <ul>
            <li><b>S&P 500:</b> {data['S&P 500']['str']}</li>
            <li><b>Nasdaq 100:</b> {data['Nasdaq 100']['str']}</li>
            <li><b>10Y Treasury:</b> {data['10-Year Yield']['str']}</li>
            <li><b>WTI Crude:</b> {data['WTI Crude']['str']}</li>
            <li><b>Bitcoin:</b> {data['Bitcoin']['str']}</li>
            <li><b>Gold:</b> {data['Gold']['str']}</li>
        </ul>
        <br>
        <h3><b>🔍 THE STORY</b></h3>
        <p><b>What Happened Yesterday:</b> [Facts from news]</p>
        <p><b>Why It Matters:</b> [Analysis]</p>
        <br>
        <h3><b>📈 WHAT ELSE IS MOVING</b></h3>
        <ul>
            <li>[News item 1]</li>
            <li>[News item 2]</li>
        </ul>
        <br>
        <h3><b>💡 THE BOTTOM LINE</b></h3>
        <p>[One sentence: what to watch]</p>
        """
    else:
        user_prompt = f"Write a brief {newsletter_type} update using the news: {real_news[:500]}"

    try:
        response = client.chat.completions.create(
            model="sonar-reasoning-pro",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            timeout=60
        )
        content = response.choices[0].message.content

        if hasattr(response, 'usage'):
            log_event(f"🤖 AI used {response.usage.total_tokens} tokens")

        clean_html = re.sub(r'```html|```', '', content).strip()
        clean_html = re.sub(r'\[\d+\]', '', clean_html)

        disclaimer = """<br><hr>
<div style="background-color: #fff3cd; padding: 15px; border: 1px solid #ffc107; margin: 20px 0;">
  <p style="margin: 0; font-size: 11px; color: #856404;">
    <b>⚠️ INVESTMENT DISCLAIMER:</b> This newsletter is for informational and educational purposes only. 
    It is NOT investment advice. Consult a licensed financial advisor before making investment decisions. 
    Past performance does not guarantee future results.
  </p>
</div>
<div style="font-size: 10px; color: #666;">
  <p><b>DISCLAIMER & DISCLOSURE:</b> For Informational Purposes Only. This communication is strictly for educational and entertainment purposes. It is not intended as an offer or solicitation for the purchase or sale of any financial instrument, nor is it intended to provide investment, legal, or tax advice. Opinions Are My Own. <b>Risk Warning:</b> Trading involves substantial risks.</p>
</div>
"""


        log_event("✅ Content generated successfully")
        return clean_html + disclaimer

    except Exception as e:
        print(f"❌ AI Error: {e}")
        log_event(f"❌ Generation failed: {e}")
        return None

# ==========================================
# 10. AUTO-SENDER
# ==========================================
def send_email(content, subject, to_email):
    msg = MIMEText(content, "html")
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ SENT to {to_email}: {subject}")
        log_event(f"✅ Email sent: {subject}")
        return True
    except Exception as e:
        print(f"❌ Email Failed: {e}")
        log_event(f"❌ Email failed: {e}")
        return False

# ==========================================
# 11. MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    log_event("=" * 60)
    log_event("🚀 Deal Diligence Newsletter - Starting Run")

    try:
        newsletter_type = get_newsletter_type()
        log_event(f"📅 Newsletter type: {newsletter_type}")

        if newsletter_type == "WEEKEND":
            log_event("⏸️ Skipping - Saturday")
            print("⏸️ No newsletter on Saturdays")
            sys.exit(0)

        market_data = get_market_data()

        is_valid, warning = validate_data(market_data)
        if not is_valid:
            print(warning)
            log_event(warning)
            send_email(f"⚠️ AUTO-ABORT: {warning}", "Deal Diligence ERROR", RECEIVER_EMAIL)
            sys.exit(1)

        save_market_snapshot(market_data, newsletter_type)

        html_content = generate_content(market_data, newsletter_type)

        if not html_content:
            error_msg = "AI content generation returned empty"
            log_event(f"❌ {error_msg}")
            send_email(f"⚠️ GENERATION ERROR: {error_msg}", "Deal Diligence ERROR", RECEIVER_EMAIL)
            sys.exit(1)

        subject_map = {
            "MONDAY": f"🎯 The Monday Setup: {datetime.now().strftime('%b %d')}",
            "FRIDAY": f"🏁 The Friday Wrap: {datetime.now().strftime('%b %d')}",
            "SUNDAY": f"📅 The Sunday Brief: Week of {datetime.now().strftime('%b %d')}",
            "WEEKDAY": f"☕ The Morning Pour: {datetime.now().strftime('%b %d')}"
        }

        subject = subject_map.get(newsletter_type, f"☕ The Morning Pour: {datetime.now().strftime('%b %d')}")
        success = send_email(html_content, subject, RECEIVER_EMAIL)

        if success:
            log_event("✅ Newsletter completed successfully")
        else:
            log_event("⚠️ Generated but email failed")

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"❌ FATAL ERROR: {e}")
        log_event(f"❌ FATAL: {e}\n{error_trace}")

        try:
            send_email(
                f"<h3>Deal Diligence Fatal Error</h3><pre>{error_trace}</pre>",
                "Deal Diligence CRITICAL ERROR",
                RECEIVER_EMAIL
            )
        except:
            pass

        sys.exit(1)
# test sync
