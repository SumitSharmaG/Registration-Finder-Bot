import os, telebot, requests, urllib3
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread

# --- RENDER KEEP-ALIVE (Do not touch) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Active!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ----------------------------------------

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))
URL = "https://msbuexam.org/StSticTCntAlL/FindForm.php"

def get_msbu_data(name):
    session = requests.Session()
    # Website ko lagega ki asli Chrome browser se request aa rahi hai
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://msbuexam.org",
        "Referer": "https://msbuexam.org/StSticTCntAlL/FindForm.php",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    try:
        # Step 1: Pehle page par ja kar session/cookies activate karna
        session.get(URL, headers=headers, verify=False, timeout=15)
        
        # Step 2: Data maangna (Multiple results handle karne ke liye)
        payload = {
            'candidateName': name,
            'fatherName': '',
            'submit': 'Search'
        }
        
        # Thoda gap de kar request bhejna (Insaan ki tarah)
        response = session.post(URL, data=payload, headers=headers, verify=False, timeout=25)
        return response.text
    except Exception as e:
        print(f"Error: {e}")
        return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🎯 **MSBU Registration Finder Updated!**\n\nBas Student ka Name bhejein, main sab details nikaal loonga.")

@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    search_name = message.text
    sent_msg = bot.reply_to(message, f"🔍 `{search_name}` dhoond raha hoon, thoda sabr rakhein...")
    
    html = get_msbu_data(search_name)
    if not html:
        bot.edit_message_text("❌ Website server respond nahi kar raha.", message.chat.id, sent_msg.message_id)
        return

    soup = BeautifulSoup(html, 'html.parser')
    
    # MSBU Table ko dhoondne ka naya tarika
    table = soup.find('table')
    
    if table:
        rows = table.find_all('tr')
        if len(rows) > 1:
            results = f"✅ **Found {len(rows)-1} Records:**\n\n"
            for row in rows[1:]:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    results += (
                        f"📝 **Form:** `{cols[0].text.strip()}`\n"
                        f"👤 **Name:** {cols[1].text.strip()}\n"
                        f"👨‍💼 **Father:** {cols[2].text.strip()}\n"
                        f"━━━━━━━━━━━━\n"
                    )
                if len(results) > 3500: # Message length safety
                    results += "\n⚠️ *List lambi hai, kuch results chhut gaye.*"
                    break
            bot.edit_message_text(results, message.chat.id, sent_msg.message_id, parse_mode='Markdown')
        else:
            bot.edit_message_text(f"❌ `{search_name}` naam se koi data nahi mila.", message.chat.id, sent_msg.message_id)
    else:
        # Agar block hue toh ye message aayega
        if "Forbidden" in html or "403" in html:
            bot.edit_message_text("🚫 Site ne block kar diya (403). Thodi der baad try karein.", message.chat.id, sent_msg.message_id)
        else:
            bot.edit_message_text("⚠️ Data nahi mil raha. Shayad naam galat hai ya site busy hai.", message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    keep_alive() # Starts Flask server for Render
    bot.polling(none_stop=True)
    
