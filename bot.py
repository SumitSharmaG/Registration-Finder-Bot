import os
import telebot
import requests
from bs4 import BeautifulSoup
import urllib3
from flask import Flask
from threading import Thread

# 1. Render Port Fix: Flask server to keep the service alive
app = Flask('')

@app.route('/')
def home():
    return "Bot is running perfectly!"

def run():
    # Render hamesha ek PORT provide karta hai
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# 2. SSL/Security Setup
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 3. Bot Configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)
URL = "https://msbuexam.org/StSticTCntAlL/FindForm.php"

# 4. Search Logic with Anti-Block Session
def fetch_msbu_data(name):
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": URL,
        "Origin": "https://msbuexam.org"
    }
    
    try:
        # Step A: Get initial cookies
        session.get(URL, headers=headers, verify=False, timeout=15)
        
        # Step B: Post Search Data
        payload = {
            'candidateName': name,
            'fatherName': '',
            'submit': 'Search'
        }
        response = session.post(URL, data=payload, headers=headers, verify=False, timeout=25)
        return response
    except Exception:
        return None

# 5. Bot Handlers
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 **MSBU Form Finder (Fixed Version) Active!**\n\nBas student ka **Full Name** bhejein.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    search_name = message.text
    sent_msg = bot.reply_to(message, f"🔍 Searching for `{search_name}`... Please wait.")
    
    response = fetch_msbu_data(search_name)
    
    if response is None:
        bot.edit_message_text("🚫 Connection Error! MSBU site respond nahi kar rahi.", message.chat.id, sent_msg.message_id)
        return

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        
        if table:
            rows = table.find_all('tr')
            if len(rows) > 1:
                results = "✅ **Found Results:**\n\n"
                # Pehle 5-6 results dikhayenge
                for row in rows[1:7]:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        results += (
                            f"📝 **Form No:** `{cols[0].text.strip()}`\n"
                            f"👤 **Name:** {cols[1].text.strip()}\n"
                            f"👨‍💼 **Father:** {cols[2].text.strip()}\n"
                            f"━━━━━━━━━━━━\n"
                        )
                bot.edit_message_text(results, message.chat.id, sent_msg.message_id, parse_mode='Markdown')
            else:
                bot.edit_message_text("❌ Is naam se koi record nahi mila.", message.chat.id, sent_msg.message_id)
        else:
            bot.edit_message_text("⚠️ Site layout changed. Website shayad block kar rahi hai.", message.chat.id, sent_msg.message_id)
    elif response.status_code == 403:
        bot.edit_message_text("🚫 Error 403: Access Denied. Website ne bot ko pehchan liya hai.", message.chat.id, sent_msg.message_id)
    else:
        bot.edit_message_text(f"❌ Website Error: {response.status_code}", message.chat.id, sent_msg.message_id)

# 6. Execution Loop
def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()  # Start Flask
    print("Bot is starting...")
    bot.polling(none_stop=True)
