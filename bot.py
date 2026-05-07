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

# --- RENDER PORT FIX (Flask Server) ---
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    # Render isi response ka wait karta hai "Success" manne ke liye
    return "Bot is Live!", 200

def run_web_server():
    # Render automatically $PORT environment variable set karta hai
    # Agar Render port nahi deta (locally), toh 10000 use hoga
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# --- BOT CONFIG & LOGIC ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8777189359:AAE3okN8Bfwf4P7umF_kku0kgIU12yVvCtw"
SEARCH_URL = "https://msbuexam.org/StSticTCntAlL/fatchformno.php"
REFERER_URL = "https://msbuexam.org/StSticTCntAlL/FindForm.php"

CHOOSE_SEARCH, ENTER_VALUE, ENTER_FATHER = range(3)

def fetch_results(payload: dict) -> str:
    try:
        time.sleep(random.uniform(2, 4))
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome','platform': 'windows','desktop': True})
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9",
            "Origin": "https://msbuexam.org",
            "Referer": REFERER_URL,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = scraper.post(SEARCH_URL, data=payload, headers=headers, timeout=30)
        if resp.status_code == 403: return "ERR_403"
        return resp.text
    except Exception as e:
        logger.error(f"Fetch Error: {e}")
        return None

def parse_html_table(html: str):
    if html == "ERR_403": return "403"
    if not html: return None
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not table: return None
    rows = table.find_all("tr")
    if len(rows) <= 1: return None
    headers = [th.get_text(strip=True) for th in rows[0].find_all(["td", "th"])]
    entries = []
    for row in rows[1:]:
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if not cells: continue
        entry_text = "".join([f"• *{h}:* `{c}`\n" for h, c in zip(headers, cells)])
        entries.append(entry_text)
    return entries

# --- COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [["👤 Candidate Name"], ["📱 Mobile Number"], ["🪪 Aadhar Number"], ["🎓 ABC ID"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("🎓 *MSBU Exam Finder Bot*\nSelect your search method:", reply_markup=reply_markup, parse_mode="Markdown")
    return CHOOSE_SEARCH

async def choose_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    mapping = {"👤 Candidate Name": "name", "📱 Mobile Number": "mobile", "🪪 Aadhar Number": "aadhar", "🎓 ABC ID": "abc"}
    if choice not in mapping: return CHOOSE_SEARCH
    context.user_data["search_type"] = mapping[choice]
    await update.message.reply_text(f"Enter {choice} details:", reply_markup=ReplyKeyboardRemove())
    return ENTER_FATHER if mapping[choice] == "name" else ENTER_VALUE

async def enter_father(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["candidate_name"] = update.message.text.strip()
    await update.message.reply_text("Enter Father's Name (or type '-' to skip):")
    return ENTER_VALUE

async def enter_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    search_type = context.user_data.get("search_type")
    value = update.message.text.strip()
    payload = {"Sname": "", "Fname": "", "Mname": "", "Mob": "", "uid": "", "abc": "", "finfom": "Proceed"}
    
    if search_type == "name":
        payload["Sname"] = context.user_data.get("candidate_name", "")
        payload["Fname"] = "" if value == "-" else value
    elif search_type == "mobile": payload["Mob"] = value
    elif search_type == "aadhar": payload["uid"] = value
    elif search_type == "abc": payload["abc"] = value

    await update.message.reply_text("🔍 Fetching results from MSBU...")
    html = fetch_results(payload)
    results = parse_html_table(html)

    if results == "403":
        await update.message.reply_text("❌ Website still blocking IP (403 Forbidden).")
    elif not results:
        await update.message.reply_text("⚠️ No record found.")
    else:
        for entry in results:
            await update.message.reply_text(entry, parse_mode="Markdown")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled. Type /start to begin.")
    return ConversationHandler.END

def main():
    # 1. Start Fake Web Server to keep Render happy
    Thread(target=run_web_server, daemon=True).start()
    
    # 2. Start Bot Polling
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
    
    logger.info("Bot logic + Port satisfaction server started.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
        
