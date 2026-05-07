import os
import logging
import cloudscraper
import time
import random
from threading import Thread
from flask import Flask
from bs4 import BeautifulSoup
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# --- WEB SERVER FOR RENDER PORT FIX ---
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "Bot is Live with Free Proxy!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN") 
SEARCH_URL = "https://msbuexam.org/StSticTCntAlL/fatchformno.php"
REFERER_URL = "https://msbuexam.org/StSticTCntAlL/FindForm.php"

CHOOSE_SEARCH, ENTER_VALUE, ENTER_FATHER = range(3)

def fetch_results(payload: dict) -> str:
    try:
        time.sleep(random.uniform(2, 4))

        # Render Environment Variables se sirf IP aur Port uthayega
        p_host = os.environ.get("PROXY_HOST")
        p_port = os.environ.get("PROXY_PORT")

        if not p_host or not p_port:
            logger.error("Proxy IP or Port missing in Environment Variables!")
            return None

        # Free Proxy Format (No Username/Password)
        proxy_url = f"http://{p_host}:{p_port}"
        proxies = {"http": proxy_url, "https": proxy_url}

        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Origin": "https://msbuexam.org",
            "Referer": REFERER_URL,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }

        resp = scraper.post(SEARCH_URL, data=payload, headers=headers, proxies=proxies, timeout=55)
        if resp.status_code == 403: return "ERR_403"
        return resp.text
    except Exception as e:
        logger.error(f"Proxy Error: {e}")
        return None

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [["👤 Candidate Name"], ["📱 Mobile Number"], ["🪪 Aadhar Number"], ["🎓 ABC ID"]]
    await update.message.reply_text("🎓 *MSBU Finder*\nMethod choose karein:", 
                                   reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True), 
                                   parse_mode="Markdown")
    return CHOOSE_SEARCH

async def choose_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    mapping = {"👤 Candidate Name": "name", "📱 Mobile Number": "mobile", "🪪 Aadhar Number": "aadhar", "🎓 ABC ID": "abc"}
    choice = update.message.text
    if choice not in mapping: return CHOOSE_SEARCH
    context.user_data["search_type"] = mapping[choice]
    await update.message.reply_text(f"✏️ Enter {choice}:", reply_markup=ReplyKeyboardRemove())
    return ENTER_FATHER if mapping[choice] == "name" else ENTER_VALUE

async def enter_father(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["candidate_name"] = update.message.text.strip()
    await update.message.reply_text("✏️ Enter Father's Name (or '-' to skip):")
    return ENTER_VALUE

async def enter_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    search_type = context.user_data.get("search_type")
    value = update.message.text.strip()
    payload = {"Sname": "", "Fname": "", "Mname": "", "Mob": "", "uid": "", "abc": "", "finfom": "Proceed"}
    
    if search_type == "name":
        payload["Sname"], payload["Fname"] = context.user_data.get("candidate_name", ""), ("" if value == "-" else value)
    elif search_type == "mobile": payload["Mob"] = value
    elif search_type == "aadhar": payload["uid"] = value
    elif search_type == "abc": payload["abc"] = value

    await update.message.reply_text("🔍 Searching via Free Proxy...")
    html = fetch_results(payload)
    
    if html == "ERR_403":
        await update.message.reply_text("❌ 403 Forbidden (Proxy Blocked)")
    elif not html:
        await update.message.reply_text("⚠️ Proxy Error: Connection failed or timed out.")
    else:
        soup = BeautifulSoup(html, "lxml")
        table = soup.find("table")
        if not table:
            await update.message.reply_text("⚠️ No record found.")
        else:
            rows = table.find_all("tr")
            headers = [td.get_text(strip=True) for td in rows[0].find_all(["td", "th"])]
            for row in rows[1:]:
                cells = [td.get_text(strip=True) for td in row.find_all("td")]
                msg = "".join([f"• *{h}:* `{c}`\n" for h, c in zip(headers, cells)])
                await update.message.reply_text(msg, parse_mode="Markdown")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

def main():
    if not TOKEN:
        logger.error("BOT_TOKEN is missing!")
        return
    Thread(target=run_web_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_search)],
            ENTER_FATHER: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_father)],
            ENTER_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))
    logger.info("Bot is active with Free Proxy Logic.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
