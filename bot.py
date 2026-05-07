import os
import logging
import requests
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

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# States
CHOOSE_SEARCH, ENTER_VALUE, ENTER_FATHER = range(3)

# URLs & Headers
SEARCH_URL = "https://msbuexam.org/StSticTCntAlL/fatchformno.php"
REFERER_URL = "https://msbuexam.org/StSticTCntAlL/FindForm.php"

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": REFERER_URL,
    "Origin": "https://msbuexam.org",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

SEARCH_OPTIONS = {
    "👤 Candidate Name": "name",
    "📱 Mobile Number": "mobile",
    "🪪 Aadhar Number": "aadhar",
    "🎓 ABC ID": "abc",
}

KEYBOARD = [[key] for key in SEARCH_OPTIONS.keys()]

# Helper Functions
def fetch_results(payload: dict) -> str:
    try:
        resp = requests.post(SEARCH_URL, data=payload, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None

def parse_html_table(html: str):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not table:
        return None

    rows = table.find_all("tr")
    if len(rows) <= 1:
        return None

    # Getting column headers (S.No, Form No, Name, etc.)
    headers = [th.get_text(strip=True) for th in rows[0].find_all(["td", "th"])]
    
    entries = []
    for row in rows[1:]:
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if not cells:
            continue
        # Zip headers and cells for clear output
        entry_text = ""
        for h, c in zip(headers, cells):
            entry_text += f"• *{h}:* `{c}`\n"
        entries.append(entry_text)
    
    return entries

# Handler Functions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_markup = ReplyKeyboardMarkup(KEYBOARD, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "🎓 *MSBU Exam Portal — Form Finder*\n\n"
        "Apna application number search karne ke liye niche diye gaye options mein se ek choose karein:",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )
    return CHOOSE_SEARCH

async def choose_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    if choice not in SEARCH_OPTIONS:
        await update.message.reply_text("❌ Please button ka use karke option select karein.")
        return CHOOSE_SEARCH

    search_type = SEARCH_OPTIONS[choice]
    context.user_data["search_type"] = search_type

    prompts = {
        "name": "✏️ *Candidate ka pura naam* enter karein:",
        "mobile": "📱 *10-digit mobile number* enter karein:",
        "aadhar": "🪪 *12-digit Aadhar number* enter karein:",
        "abc": "🎓 *12-digit ABC ID* enter karein:",
    }

    await update.message.reply_text(
        prompts[search_type],
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ENTER_FATHER if search_type == "name" else ENTER_VALUE

async def enter_father(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["candidate_name"] = update.message.text.strip()
    await update.message.reply_text(
        "✏️ *Father's Name* enter karein (Skip karne ke liye `-` type karein):",
        parse_mode="Markdown"
    )
    return ENTER_VALUE

async def enter_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    search_type = context.user_data.get("search_type")
    value = update.message.text.strip()
    
    payload = {"Sname": "", "Fname": "", "Mname": "", "Mob": "", "uid": "", "abc": "", "finfom": "Proceed"}

    if search_type == "name":
        payload["Sname"] = context.user_data.get("candidate_name", "")
        payload["Fname"] = "" if value == "-" else value
    elif search_type == "mobile":
        if len(value) != 10 or not value.isdigit():
            await update.message.reply_text("❌ Galat mobile number! 10 digits enter karein.")
            return ENTER_VALUE
        payload["Mob"] = value
    elif search_type in ["aadhar", "abc"]:
        if len(value) != 12 or not value.isdigit():
            await update.message.reply_text(f"❌ Galat ID! 12 digits enter karein.")
            return ENTER_VALUE
        if search_type == "aadhar": payload["uid"] = value
        else: payload["abc"] = value

    await update.message.reply_text("🔍 Search jari hai, kripya pratiksha karein...")
    
    html = fetch_results(payload)
    if not html:
        await update.message.reply_text("❌ Server se response nahi mila. Dobara try karein. /start")
        return ConversationHandler.END

    results = parse_html_table(html)
    if not results:
        await update.message.reply_text("⚠️ *No Record Found!* Details check karke /start karein.", parse_mode="Markdown")
        return ConversationHandler.END

    await update.message.reply_text(f"✅ *{len(results)} record(s) mile:*", parse_mode="Markdown")
    for entry in results:
        await update.message.reply_text(entry, parse_mode="Markdown")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Search cancel kar diya gaya. /start", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    # Aapka Bot Token yahan integrate kar diya gaya hai
    TOKEN = "8777189359:AAE3okN8Bfwf4P7umF_kku0kqIUi2yVvCtw"
    
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
    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
