import os
import logging
import cloudscraper
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

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Config
TOKEN = "8777189359:AAE3okN8Bfwf4P7umF_kku0kgIU12yVvCtw" # Screenshot wala token
SEARCH_URL = "https://msbuexam.org/StSticTCntAlL/fatchformno.php"
REFERER_URL = "https://msbuexam.org/StSticTCntAlL/FindForm.php"

# States
CHOOSE_SEARCH, ENTER_VALUE, ENTER_FATHER = range(3)

# Headers (Enhanced for Cloudflare bypass)
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://msbuexam.org",
    "Referer": REFERER_URL,
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
}

SEARCH_OPTIONS = {
    "👤 Candidate Name": "name",
    "📱 Mobile Number": "mobile",
    "🪪 Aadhar Number": "aadhar",
    "🎓 ABC ID": "abc",
}

KEYBOARD = [[key] for key in SEARCH_OPTIONS.keys()]

def fetch_results(payload: dict) -> str:
    try:
        # Cloudscraper cloudflare security bypass karne mein help karega
        scraper = cloudscraper.create_scraper(browser={'browser': 'firefox', 'platform': 'windows', 'mobile': False})
        resp = scraper.post(SEARCH_URL, data=payload, headers=HEADERS, timeout=25)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        logger.error(f"Fetch Error: {e}")
        return None

def parse_html_table(html: str):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not table:
        return None

    rows = table.find_all("tr")
    if len(rows) <= 1:
        return None

    headers = [th.get_text(strip=True) for th in rows[0].find_all(["td", "th"])]
    entries = []
    for row in rows[1:]:
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if not cells: continue
        entry_text = ""
        for h, c in zip(headers, cells):
            entry_text += f"• *{h}:* `{c}`\n"
        entries.append(entry_text)
    return entries

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_markup = ReplyKeyboardMarkup(KEYBOARD, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "🎓 *MSBU Exam — Form Finder*\n\nEk search option choose karein:",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )
    return CHOOSE_SEARCH

async def choose_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    if choice not in SEARCH_OPTIONS:
        return CHOOSE_SEARCH

    search_type = SEARCH_OPTIONS[choice]
    context.user_data["search_type"] = search_type

    prompts = {
        "name": "✏️ *Candidate Name* likhein:",
        "mobile": "📱 *10-digit Mobile Number* likhein:",
        "aadhar": "🪪 *12-digit Aadhar Number* likhein:",
        "abc": "🎓 *12-digit ABC ID* likhein:",
    }
    await update.message.reply_text(prompts[search_type], parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    return ENTER_FATHER if search_type == "name" else ENTER_VALUE

async def enter_father(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["candidate_name"] = update.message.text.strip()
    await update.message.reply_text("✏️ *Father's Name* enter karein (Nahi pata toh `-` type karein):", parse_mode="Markdown")
    return ENTER_VALUE

async def enter_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    search_type = context.user_data.get("search_type")
    value = update.message.text.strip()
    payload = {"Sname": "", "Fname": "", "Mname": "", "Mob": "", "uid": "", "abc": "", "finfom": "Proceed"}

    if search_type == "name":
        payload["Sname"] = context.user_data.get("candidate_name", "")
        payload["Fname"] = "" if value == "-" else value
    elif search_type == "mobile":
        payload["Mob"] = value
    elif search_type == "aadhar":
        payload["uid"] = value
    elif search_type == "abc":
        payload["abc"] = value

    await update.message.reply_text("🔍 Searching... Please wait.")
    html = fetch_results(payload)
    
    if not html:
        await update.message.reply_text("❌ Error: Website ne request block kar di. /start")
        return ConversationHandler.END

    results = parse_html_table(html)
    if not results:
        await update.message.reply_text("⚠️ No Record Found! Check details and /start again.")
    else:
        for entry in results:
            await update.message.reply_text(entry, parse_mode="Markdown")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Search cancelled. /start", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_search)],
            ENTER_FATHER: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_father)],
            ENTER_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
    logger.info("Bot is active...")
    app.run_polling()

if __name__ == "__main__":
    main()
