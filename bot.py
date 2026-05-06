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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

CHOOSE_SEARCH, ENTER_VALUE, ENTER_FATHER = range(3)

SEARCH_URL = "https://msbuexam.org/StSticTCntAlL/fatchformno.php"
REFERER_URL = "https://msbuexam.org/StSticTCntAlL/FindForm.php"

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": REFERER_URL,
    "Origin": "https://msbuexam.org",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "*/*",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
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
        resp = requests.post(SEARCH_URL, data=payload, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        logger.error("Request failed: %s", e)
        return None


def parse_html_table(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not table:
        return None

    rows = table.find_all("tr")
    if len(rows) <= 1:
        return None

    lines = []
    headers = [th.get_text(strip=True) for th in rows[0].find_all("td")]

    for row in rows[1:]:
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if not cells:
            continue
        entry = []
        for h, c in zip(headers, cells):
            entry.append(f"*{h}:* {c}")
        lines.append("\n".join(entry))

    return lines


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_markup = ReplyKeyboardMarkup(KEYBOARD, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "🎓 *MSBU Exam Portal — Form Finder Bot*\n\n"
        "Apna application number dhundhne ke liye ek search option choose karein:\n\n"
        "• Candidate Name\n"
        "• Mobile Number\n"
        "• Aadhar Number\n"
        "• ABC ID",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )
    return CHOOSE_SEARCH


async def choose_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    if choice not in SEARCH_OPTIONS:
        await update.message.reply_text("❌ Please keyboard se ek option choose karein.")
        return CHOOSE_SEARCH

    search_type = SEARCH_OPTIONS[choice]
    context.user_data["search_type"] = search_type

    prompts = {
        "name": "✏️ *Candidate ka naam* enter karein (pura naam likhein):",
        "mobile": "📱 *10-digit mobile number* enter karein:",
        "aadhar": "🪪 *12-digit Aadhar number* enter karein:",
        "abc": "🎓 *12-digit ABC ID* enter karein:",
    }

    await update.message.reply_text(
        prompts[search_type],
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )

    if search_type == "name":
        return ENTER_FATHER
    return ENTER_VALUE


async def enter_father(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    candidate_name = update.message.text.strip()
    if not candidate_name:
        await update.message.reply_text("❌ Naam khali nahi hona chahiye. Dobara try karein:")
        return ENTER_FATHER

    context.user_data["candidate_name"] = candidate_name
    await update.message.reply_text(
        "✏️ *Father's naam* enter karein _(optional — skip karne ke liye '-' type karein)_:",
        parse_mode="Markdown",
    )
    return ENTER_VALUE


async def enter_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    search_type = context.user_data.get("search_type")
    value = update.message.text.strip()

    payload = {
        "Sname": "",
        "Fname": "",
        "Mname": "",
        "Mob": "",
        "uid": "",
        "abc": "",
        "finfom": "Proceed",
    }

    if search_type == "name":
        payload["Sname"] = context.user_data.get("candidate_name", "")
        payload["Fname"] = "" if value == "-" else value
    elif search_type == "mobile":
        if not value.isdigit() or len(value) != 10:
            await update.message.reply_text("❌ 10-digit mobile number enter karein (sirf numbers):")
            return ENTER_VALUE
        payload["Mob"] = value
    elif search_type == "aadhar":
        if not value.isdigit() or len(value) != 12:
            await update.message.reply_text("❌ 12-digit Aadhar number enter karein (sirf numbers):")
            return ENTER_VALUE
        payload["uid"] = value
    elif search_type == "abc":
        if not value.isdigit() or len(value) != 12:
            await update.message.reply_text("❌ 12-digit ABC ID enter karein (sirf numbers):")
            return ENTER_VALUE
        payload["abc"] = value

    await update.message.reply_text("🔍 Search ho raha hai, thoda wait karein...")

    html = fetch_results(payload)

    if html is None:
        await update.message.reply_text(
            "❌ Server se connect nahi ho paya. Thodi der baad dobara try karein.\n\n"
            "/start karein naya search karne ke liye."
        )
        return ConversationHandler.END

    entries = parse_html_table(html)

    if not entries:
        await update.message.reply_text(
            "⚠️ *Koi record nahi mila!*\n\n"
            "• Naam exactly waise likhein jaise form mein diya tha\n"
            "• Dusra search type try karein\n\n"
            "/start karein dobara search karne ke liye.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    count = len(entries)
    header_msg = f"✅ *{count} record{'s' if count > 1 else ''} mila{'e' if count > 1 else ''}!*\n\n"
    await update.message.reply_text(header_msg, parse_mode="Markdown")

    for i, entry in enumerate(entries, 1):
        msg = f"📋 *Record {i}*\n{'─' * 20}\n{entry}"
        await update.message.reply_text(msg, parse_mode="Markdown")

    await update.message.reply_text(
        "━━━━━━━━━━━━━━━━━━━\n"
        "🔁 Naya search karne ke liye /start karein.",
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "❌ Search cancel ho gaya.\n/start karein dobara shuru karne ke liye.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling update: %s", context.error)


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable not set!")

    app = Application.builder().token(token).build()

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
    app.add_error_handler(error_handler)

    logger.info("Bot chal raha hai...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
