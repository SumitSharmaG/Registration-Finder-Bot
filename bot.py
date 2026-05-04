import os
import telebot
import cloudscraper
import urllib3
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread

# --- SECTION 1: RENDER DEPLOYMENT FIX (Do Not Change) ---
# Ye hissa Render par "Port Scan Timeout" error ko rokta hai
app = Flask('')

@app.route('/')
def home():
    return "Bot is Live and Bypassing Security!"

def run():
    # Render hamesha PORT environment variable provide karta hai
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- SECTION 2: BOT LOGIC & SECURITY BYPASS ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))

# MSBU ki asli data file (Source code se mili)
DATA_URL = "https://msbuexam.org/StSticTCntAlL/fatchformno.php"
REFERER_URL = "https://msbuexam.org/StSticTCntAlL/FindForm.php"

def get_msbu_data(name):
    # Cloudscraper Cloudflare protection ko handle karta hai
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": REFERER_URL,
        "Origin": "https://msbuexam.org",
        "X-Requested-With": "XMLHttpRequest" # AJAX request mimic karne ke liye
    }
    
    try:
        # Form fields jo website ke code mein 'name' attribute mein hain
        payload = {
            'Sname': name,     # Candidate Name
            'Fname': '',       # Father Name (Khali rakha hai as per your need)
            'Mname': '',       # Mother Name
            'Mob': '',         # Mobile
            'uid': '',         # Aadhar
            'abc': '',         # ABC ID
            'fno': '',         # Form No
            'tzone': '5.5',    # SABSE ZAROORI: IST (India) Timezone Bypass
            'finfom': 'Proceed'
        }
        
        # Request bhej rahe hain
        response = scraper.post(DATA_URL, data=payload, headers=headers, timeout=30)
        return response.text
    except Exception as e:
        print(f"Bypass Error: {e}")
        return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ **MSBU Finder (Security Bypass) Active!**\n\nSirf Student ka Name bhejein, main details nikaal loonga.")

@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    search_name = message.text
    sent_msg = bot.reply_to(message, f"🔎 `{search_name}` ke records dhoond raha hoon...")
    
    html_res = get_msbu_data(search_name)
    
    if not html_res:
        bot.edit_message_text("❌ Website ne connection block kar diya.", message.chat.id, sent_msg.message_id)
        return

    # Website ka result table format mein hota hai
    if "tr" in html_res.lower() and "td" in html_res.lower():
        soup = BeautifulSoup(html_res, 'html.parser')
        rows = soup.find_all('tr')
        
        if len(rows) > 0:
            res_msg = f"✅ **Found Records for {search_name}:**\n\n"
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    res_msg += (
                        f"📝 **Form:** `{cols[0].text.strip()}`\n"
                        f"👤 **Name:** {cols[1].text.strip()}\n"
                        f"👨‍💼 **Father:** {cols[2].text.strip()}\n"
                        f"━━━━━━━━━━━━\n"
                    )
                if len(res_msg) > 3800: break
            bot.edit_message_text(res_msg, message.chat.id, sent_msg.message_id, parse_mode='Markdown')
        else:
            bot.edit_message_text(f"❌ `{search_name}` naam ka koi record nahi mila.", message.chat.id, sent_msg.message_id)
    else:
        # Agar website koi error message bhej rahi ho (jaise "No Record Found")
        clean_text = BeautifulSoup(html_res, "html.parser").get_text().strip()
        if len(clean_text) > 2:
            bot.edit_message_text(f"📝 **Result:** {clean_text}", message.chat.id, sent_msg.message_id)
        else:
            bot.edit_message_text("❌ Data nahi mila. Shayad site ne bot ko block kiya hai.", message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    # Flask server start karna taaki Render 'Live' rahe
    keep_alive()
    # Bot start karna
    bot.polling(none_stop=True)
    
