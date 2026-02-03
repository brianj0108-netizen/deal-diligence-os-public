"""
telegram_brain.py

Public demo of a Telegram + Notion + Perplexity "personal OS".

Features (example configuration):

- research [topic]
    → Deep-dive HTML report emailed via Gmail.

- Natural stock questions
    e.g. "is TSLA a good buy?"
    → Telegram summary + optional email report.

- paycheck [amount]
    → Logs a paycheck into a Notion "Paycheck Tracker" DB, split into:
       * Needs (50%), Wants (20%), Debt (15%), Savings (15%), Investments (0 by default).

- J: [text]
    → Saves to a private Journal DB in Notion.

- Any other text
    → Saves to a Life RPG DB in Notion with a simple "class" + XP system:

        Saver    – saving / budgeting / investing
        Scholar  – studying / learning
        Athlete  – workouts / runs
        Creator  – building / writing / creating
        Explorer – everything else

All secrets / IDs come from keys.local.txt via config_public.py.
See keys.example.txt for required keys.
"""

import time
import re
import sys
from datetime import datetime

import requests
import smtplib, ssl
from email.mime_text import MIMEText  # type: ignore

from openai import OpenAI
from config_public import (
    TELEGRAM_TOKEN,
    NOTION_KEY,
    RPG_DATABASE_ID,
    JOURNAL_DATABASE_ID,
    PAYCHECK_DATABASE_ID,
    PERPLEXITY_KEY,
    EMAIL_SENDER,
    EMAIL_PASSWORD,
    EMAIL_RECEIVER,
)

# ==========================================
# 1. PERPLEXITY + EMAIL HELPERS
# ==========================================

client = OpenAI(api_key=PERPLEXITY_KEY, base_url="https://api.perplexity.ai") if PERPLEXITY_KEY else None


def send_telegram(chat_id, text: str) -> None:
    """Send a plain-text or Markdown message to Telegram."""
    if not TELEGRAM_TOKEN:
        print("❌ Missing TELEGRAM_TOKEN in keys.local.txt")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}

    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            print(f"❌ Telegram error: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"⚠️ Telegram send error: {e}")


def send_email(subject: str, body_html: str) -> bool:
    """Send HTML email via Gmail."""
    if not (EMAIL_SENDER and EMAIL_PASSWORD and EMAIL_RECEIVER):
        print("❌ Missing EMAIL_* values in keys.local.txt")
        return False

    try:
        msg = MIMEText(body_html, "html")
        msg["Subject"] = subject
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        return True
    except Exception as e:
        print(f"❌ Email Error: {e}")
        return False


def run_stock_analysis(query: str, chat_id: int):
    """Real-time-style stock analysis: Telegram summary + HTML email."""
    if not client:
        send_telegram(chat_id, "⚠️ Perplexity API key missing; cannot run stock analysis.")
        return False, "Missing PERPLEXITY_KEY"

    print(f"📊 Analyzing stock: {query}")
    system_prompt = (
        "You are a professional stock analyst. "
        "Provide a concise, timely investment analysis with:\n"
        "1. Current price and today's move\n"
        "2. Recent news and catalysts\n"
        "3. Technical outlook (trend, key levels)\n"
        "4. Fundamental snapshot\n"
        "5. Clear BUY/HOLD/SELL with reasoning.\n"
        "Use Markdown. No citation brackets."
    )
    analysis_query = (
        f"{query} - Provide current price, recent news, technical analysis, "
        "fundamentals, and a clear recommendation."
    )

    try:
        response = client.chat.completions.create(
            model="sonar-reasoning-pro",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": analysis_query},
            ],
            timeout=60,
        )
        content = response.choices[0].message.content

        # Quick summary for Telegram (first 2–3 sentences)
        sentences = content.split(".")
        quick_summary = ". ".join(sentences[:3]).strip()
        if quick_summary and not quick_summary.endswith("."):
            quick_summary += "."

        # Strip any citation tags
        content = re.sub(r"\[\d+\]|\[web:\d+\]|\[cite:\d+\]", "", content)

        telegram_msg = (
            f"*STOCK ANALYSIS*\n\n{quick_summary}\n\n"
            "_Full report sent to email if configured._"
        )
        send_telegram(chat_id, telegram_msg)

        # Simple Markdown → HTML
        content_html = re.sub(
            r"^### (.*?)$",
            r"<h3 style=\"color:#1a5490;margin-top:25px;\">\1</h3>",
            content,
            flags=re.MULTILINE,
        )
        content_html = re.sub(
            r"^## (.*?)$",
            r"<h2 style=\"color:#004d40;margin-top:30px;border-bottom:1px solid #ccc;\">\1</h2>",
            content_html,
            flags=re.MULTILINE,
        )
        content_html = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", content_html)
        content_html = re.sub(
            r"^\- (.*?)$",
            r"<li style=\"margin-bottom:8px;\">\1</li>",
            content_html,
            flags=re.MULTILINE,
        )
        content_html = re.sub(
            r"(<li.*?</li>\n?)+",
            r"<ul style=\"margin:15px 0;padding-left:25px;\">\g<0></ul>",
            content_html,
            flags=re.DOTALL,
        )
        content_html = re.sub(r"\n\n", "<br><br>", content_html)

        html_body = f"""
        <html>
          <body style="font-family: Georgia, serif; color:#2c3e50; background-color:#f9f9f9;">
            <div style="max-width:700px; margin:0 auto; padding:30px; background:white;">
              <h1 style="color:#1a5490; font-size:28px; margin-bottom:10px;">
                STOCK ANALYSIS
              </h1>
              <p style="color:#7f8c8d; font-size:13px; margin-bottom:30px;">
                {query} • Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
              </p>
              <div style="font-size:16px; line-height:1.8;">
                {content_html}
              </div>
              <hr style="margin:40px 0 20px 0; border:none; border-top:1px solid #e0e0e0;">
              <p style="font-size:12px; color:#95a5a6; text-align:center;">
                Demo Finance OS • Real-Time Analysis via Perplexity
              </p>
            </div>
          </body>
        </html>
        """
        success = send_email(f"Stock Analysis: {query}", html_body)
        return success, "Complete" if success else "Email Failed"
    except Exception as e:
        print(f"❌ Stock analysis error: {e}")
        return False, f"Error: {e}"


def run_research_and_email(query: str):
    """Ask Perplexity for a deep-dive report, convert to HTML, and email it."""
    if not client:
        return False, "Missing PERPLEXITY_KEY"

    print(f"🕵️ Researching: {query}")
    system_prompt = (
        "You are a top-tier financial / market analyst. "
        "Write a clear deep-dive report in Markdown with:\n"
        "## Overview, ## Recent Developments, ## Fundamentals (if relevant), "
        "## Risks, ## Conclusion.\n"
        "No citation numbers or reference brackets."
    )

    try:
        response = client.chat.completions.create(
            model="sonar-reasoning-pro",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            timeout=90,
        )
        content = response.choices[0].message.content

        content = re.sub(r"\[\d+\]|\[web:\d+\]|\[cite:\d+\]", "", content)

        content_html = re.sub(
            r"^### (.*?)$",
            r"<h3 style=\"color:#1a5490;margin-top:25px;\">\1</h3>",
            content,
            flags=re.MULTILINE,
        )
        content_html = re.sub(
            r"^## (.*?)$",
            r"<h2 style=\"color:#004d40;margin-top:30px;border-bottom:1px solid #ccc;\">\1</h2>",
            content_html,
            flags=re.MULTILINE,
        )
        content_html = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", content_html)
        content_html = re.sub(
            r"^\- (.*?)$",
            r"<li style=\"margin-bottom:8px;\">\1</li>",
            content_html,
            flags=re.MULTILINE,
        )
        content_html = re.sub(
            r"(<li.*?</li>\n?)+",
            r"<ul style=\"margin:15px 0;padding-left:25px;\">\g<0></ul>",
            content_html,
            flags=re.DOTALL,
        )
        content_html = re.sub(r"\n\n", "<br><br>", content_html)

        html_body = f"""
        <html>
          <body style="font-family: Georgia, serif; color:#2c3e50; background-color:#f9f9f9;">
            <div style="max-width:700px; margin:0 auto; padding:30px; background:white;">
              <h1 style="color:#1a5490; font-size:28px; margin-bottom:10px;">
                🕵️ {query.upper()}
              </h1>
              <p style="color:#7f8c8d; font-size:13px; margin-bottom:30px;">
                Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
              </p>
              <div style="font-size:16px; line-height:1.8;">
                {content_html}
              </div>
              <hr style="margin:40px 0 20px 0; border:none; border-top:1px solid #e0e0e0;">
              <p style="font-size:12px; color:#95a5a6; text-align:center;">
                Demo Finance OS • Powered by Perplexity
              </p>
            </div>
          </body>
        </html>
        """
        success = send_email(f"Research Report: {query.upper()}", html_body)
        return success, "Email Sent" if success else "Email Failed"
    except Exception as e:
        print(f"❌ Research error: {e}")
        return False, f"Error: {e}"


# ==========================================
# 2. NOTION HELPERS (RPG / JOURNAL / PAYCHECK)
# ==========================================

def parse_money_value(text: str):
    """Extract money like '50k', '2.5m', '$100k' into integer dollars."""
    lower = text.lower()
    match = re.search(r"[\$]?\s*(\d+\.?\d*)\s*([km])", lower)
    if not match:
        return None
    number = float(match.group(1))
    suffix = match.group(2)
    if suffix == "k":
        return int(number * 1_000)
    if suffix == "m":
        return int(number * 1_000_000)
    return None


def detect_rpg_class(text: str):
    """
    Generic RPG "class" and XP:

    - Saver:   saving, budgeting, investing money
    - Scholar: studying, exams, learning
    - Athlete: workouts, runs, fitness
    - Creator: building, writing, creating things
    - Explorer (default): everything else
    """
    lower = text.lower()

    if any(x in lower for x in ["save", "saving", "budget", "invest", "money"]):
        return {"Class": {"select": {"name": "Saver"}}, "XP": {"number": 50}}

    if any(x in lower for x in ["study", "exam", "course", "learn", "class"]):
        return {"Class": {"select": {"name": "Scholar"}}, "XP": {"number": 30}}

    if any(x in lower for x in ["workout", "gym", "run", "lift", "exercise"]):
        return {"Class": {"select": {"name": "Athlete"}}, "XP": {"number": 30}}

    if any(x in lower for x in ["write", "build", "create", "record", "design"]):
        return {"Class": {"select": {"name": "Creator"}}, "XP": {"number": 20}}

    return {"Class": {"select": {"name": "Explorer"}}, "XP": {"number": 10}}


def save_to_notion(database_id: str, content: str, tag_name: str = "Mobile Entry") -> None:
    """Save content to a Notion database (RPG or Journal)."""
    if not (NOTION_KEY and database_id):
        print("❌ Missing NOTION_KEY or database ID")
        return

    print(f"📝 Saving to Notion: {content[:50]}")
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    today = datetime.now().strftime("%Y-%m-%d")

    if database_id == RPG_DATABASE_ID:
        aum_value = None
        quest_title = content[:100]

        if "aum" in content.lower():
            aum_value = parse_money_value(content)
            if aum_value:
                quest_title = f"AUM Gained: ${aum_value:,}"

        class_xp = detect_rpg_class(content)

        properties = {
            "Quest": {"title": [{"text": {"content": quest_title}}]},
            "Date": {"date": {"start": today}},
            "Topic": {"multi_select": [{"name": tag_name}]},
        }
        properties.update(class_xp)
        if aum_value is not None:
            properties["AUM"] = {"number": aum_value}

        payload = {
            "parent": {"database_id": database_id},
            "properties": properties,
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": content}}
                        ]
                    },
                }
            ],
        }
    else:
        payload = {
            "parent": {"database_id": database_id},
            "properties": {
                "Name": {"title": [{"text": {"content": content[:100]}}]},
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": content}}
                        ]
                    },
                }
            ],
        }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code != 200:
            print(f"❌ Notion Error: {resp.status_code} {resp.text}")
        else:
            print("✅ Saved to Notion successfully")
    except Exception as e:
        print(f"❌ Notion request error: {e}")


def save_paycheck_to_notion(net_amount: float):
    """
    Generic paycheck allocation:

        50% Needs       (rent, bills, groceries)
        20% Wants       (fun, lifestyle)
        15% Debt        (any loans / credit cards)
        15% Savings     (emergency fund or short-term goals)

    Writes into a Notion "Paycheck Tracker" DB with columns:
        Check #, Date, Net Amount, Needs, Wants, Debt, Savings, Investments
    """
    if not PAYCHECK_DATABASE_ID:
        return False, "PAYCHECK_DATABASE_ID missing"
    if not NOTION_KEY:
        return False, "NOTION_KEY missing"

    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    alloc = {
        "Needs": round(net_amount * 0.50, 2),
        "Wants": round(net_amount * 0.20, 2),
        "Debt": round(net_amount * 0.15, 2),
        "Savings": round(net_amount * 0.15, 2),
    }
    used_total = sum(alloc.values())
    checking_remaining = round(net_amount - used_total, 2)

    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    title = f"Paycheck - {today_str}"

    properties = {
        "Check #": {"title": [{"text": {"content": title}}]},
        "Date": {"date": {"start": today_str}},
        "Net Amount": {"number": float(net_amount)},
        "Needs": {"number": float(alloc["Needs"])},
        "Wants": {"number": float(alloc["Wants"])},
        "Debt": {"number": float(alloc["Debt"])},
        "Savings": {"number": float(alloc["Savings"])},
        "Investments": {"number": 0.0},
    }

    payload = {
        "parent": {"database_id": PAYCHECK_DATABASE_ID},
        "properties": properties,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code != 200:
            print(f"❌ Paycheck Notion Error: {resp.status_code} {resp.text}")
            return False, f"Notion error {resp.status_code}"
    except Exception as e:
        print(f"❌ Paycheck request error: {e}")
        return False, str(e)

    lines = [
        f"💰 *Paycheck Logged*: ${net_amount:,.2f}",
        "",
        "*Allocations*:",
        f"- Needs: ${alloc['Needs']:,.2f}",
        f"- Wants: ${alloc['Wants']:,.2f}",
        f"- Debt: ${alloc['Debt']:,.2f}",
        f"- Savings: ${alloc['Savings']:,.2f}",
        "",
        f"🏦 *Checking Remaining* (per Notion formula): about ${checking_remaining:,.2f}",
        "",
        "_Customize these buckets and percentages in `save_paycheck_to_notion`._",
    ]
    return True, "\n".join(lines)


# ==========================================
# 3. MAIN LOOP (TELEGRAM ROUTING)
# ==========================================

def main():
    print("🤖 DEMO ASSISTANT ONLINE (Research + Stock + RPG + Paycheck)...")

    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN missing; exiting.")
        sys.exit(1)

    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset + 1}"
            resp = requests.get(url, timeout=30).json()

            if "result" in resp:
                for update in resp["result"]:
                    offset = update["update_id"]
                    if "message" not in update:
                        continue

                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"].get("text", "") or ""
                    print(f"📩 Received: {text}")
                    text_lower = text.lower().strip()

                    # 0. HELP MENU
                    if text_lower in ["/help", "/triggers", "help", "triggers"]:
                        help_msg = """
*DEMO PERSONAL OS - COMMAND GUIDE*

*RESEARCH & ANALYSIS*
- `research [topic]` → Deep-dive email report
- Ask "is [stock] a good buy?" → Telegram summary + email

*PAYCHECK TRACKER*
- `paycheck [amount]` → Log paycheck + simple allocation into Notion
  Example: `paycheck 1500` or `paycheck $1,500`

*NOTION JOURNAL*
- `J: [text]` → Save to Private Journal DB
- Any other text → Save to Life RPG DB (with XP + Class)

*RPG CLASSES (example logic)*
- *Saver*: saving, budgeting, investing money
- *Scholar*: studying, exams, learning
- *Athlete*: workouts, gym, running
- *Creator*: building, writing, creating
- *Explorer*: everything else

*AUM TRACKING*
- `Added 50k AUM` → AUM column = $50,000, Quest = "AUM Gained: $50,000"
- Works with: 50k, 2.5m, $100k, etc.

*ℹ OTHER*
- `/help` or `triggers` → Show this menu
"""
                        send_telegram(chat_id, help_msg)
                        continue

                    # 1. PAYCHECK TRACKER
                    if text_lower.startswith("paycheck"):
                        match = re.search(r"([\d,]+(\.\d+)?)", text_lower)
                        if not match:
                            send_telegram(chat_id, "⚠️ Could not find an amount. Use: `paycheck 1500`")
                            continue
                        amt_str = match.group(1).replace(",", "")
                        try:
                            net_amount = float(amt_str)
                        except ValueError:
                            send_telegram(chat_id, "⚠️ Invalid number. Use: `paycheck 1500`")
                            continue

                        send_telegram(chat_id, f"📊 Logging paycheck for ${net_amount:,.2f} into Notion...")
                        success, msg = save_paycheck_to_notion(net_amount)
                        if success:
                            send_telegram(chat_id, msg)
                        else:
                            send_telegram(chat_id, f"❌ Failed to save paycheck: {msg}")
                        continue

                    # 2. RESEARCH REPORTS
                    if text_lower.startswith("research"):
                        send_telegram(chat_id, "🕵️ Generating report... check your inbox in ~1–2 minutes.")
                        query = text[8:].strip()
                        success, msg = run_research_and_email(query)
                        if success:
                            send_telegram(chat_id, "✅ Report sent to email.")
                        else:
                            send_telegram(chat_id, f"❌ Failed: {msg}")
                        continue

                    # 3. STOCK ANALYSIS (simple natural-language detection)
                    stock_keywords = ["buy", "sell", "invest", "stock", "ticker", "shares"]
                    has_stock_keyword = any(k in text_lower for k in stock_keywords)
                    is_question = any(q in text_lower for q in ["is ", "should i", "what do you think"])
                    if has_stock_keyword and is_question and len(text_lower.split()) < 40:
                        send_telegram(chat_id, "📈 Analyzing with market data...")
                        success, msg = run_stock_analysis(text, chat_id)
                        if not success:
                            send_telegram(chat_id, f"❌ Failed: {msg}")
                        continue

                    # 4. PRIVATE JOURNAL
                    if text_lower.startswith("j:") or text_lower.startswith("journal:"):
                        clean_text = text.split(":", 1)[1].strip()
                        save_to_notion(JOURNAL_DATABASE_ID, clean_text, tag_name="Private")
                        send_telegram(chat_id, "📓 Saved to Private Journal.")
                        continue

                    # 5. DEFAULT: LIFE RPG
                    save_to_notion(RPG_DATABASE_ID, text, tag_name="Mobile Entry")
                    send_telegram(chat_id, "✅ Saved to Life RPG.")

            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Main loop error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
