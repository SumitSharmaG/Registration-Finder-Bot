import os
import time
import random
import telebot
import cloudscraper
import urllib3
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------- FLASK (KEEP ALIVE) ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is live"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run, daemon=True).start()

# ---------------- BOT ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env variable missing")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

DATA_URL = "https://msbuexam.org/StSticTCntAlL/fatchformno.php"
REFERER_URL = "https://msbuexam.org/StSticTCntAlL/FindForm.php"

# Optional: single proxy from env (use only if you have permission)
# Format: http://user:pass@host:port  OR http://host:port
PROXY_URL = os.environ.get("HTTP_PROXY") or os.environ.get("HTTPS_PROXY")

def build_scraper():
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )
    if PROXY_URL:
        scraper.proxies = {
            "http": PROXY_URL,
            "https": PROXY_URL
        }
    return scraper

def fetch_once(scraper, name: str):
    # 1) Warm-up request to get cookies/session
    scraper.get(REFERER_URL, timeout=20)

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": REFERER_URL,
        "Origin": "https://msbuexam.org",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
        "Connection": "keep-alive",
    }

    payload = {
        "Sname": name,
        "Fname": "",
        "Mname": "",
        "Mob": "",
        "uid": "",
        "abc": "",
        "fno": "",
        "tzone": "5.5",
        "finfom": "Proceed",
    }

    resp = scraper.post(DATA_URL, data=payload, headers=headers, timeout=25)
    return resp

def get_msbu_data(name: str, max_retries: int = 3):
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            scraper = build_scraper()
            resp = fetch_once(scraper, name)

            if resp.status_code == 200 and resp.text:
                return resp.text

            last_err = f"HTTP {resp.status_code}"
        except Exception as e:
            last_err = str(e)

        # backoff with jitter
        sleep_s = min(10, 2 ** attempt) + random.uniform(0.2, 1.0)
        time.sleep(sleep_s)

    print("Failed after retries:", last_err)
    return None

def parse_result(html: str, query_name: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr")

    if rows:
        out = f"*Results for {query_name}:*\n\n"
        count = 0
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3:
                out += (
                    f"📑 *Form:* `{cols[0].text.strip()}`\n"
                    f"👤 *Name:* {cols[1].text.strip()}\n"
                    f"👨‍👦 *Father:* {cols[2].text.strip()}\n"
                    f"──────────────\n"
                )
                count += 1
                if len(out) > 3800:
                    break

        if count == 0:
            clean = soup.get_text().strip()
            return f"No structured rows.\n\n{clean[:3500]}"
        return out

    clean = soup.get_text().strip()
    return f"No records found.\n\n{clean[:3500]}"

# ---------------- HANDLERS ----------------
@bot.message_handler(commands=["start"])
def start(msg):
    bot.reply_to(
        msg,
        "MSBU Finder Bot ready.\n\nStudent ka *name* bhejo."
    )

@bot.message_handler(func=lambda m: True)
def handle(m):
    name = (m.text or "").strip()
    if not name:
        bot.reply_to(m, "Please valid name bhejo.")
        return

    sent = bot.reply_to(m, f"🔎 Searching `{name}` ...")

    html = get_msbu_data(name)
    if not html:
        bot.edit_message_text(
            "❌ Data fetch nahi ho paya (blocked / network issue).",
            m.chat.id,
            sent.message_id
        )
        return

    result = parse_result(html, name)
    bot.edit_message_text(result, m.chat.id, sent.message_id)

# ---------------- RUN ----------------
if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
