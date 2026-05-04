import os, telebot, cloudscraper, urllib3
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread

# Render Keep-Alive
app = Flask('')
@app.route('/')
def home(): return "Bot is Online with IST Bypass!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))

# --- ASLI ENDPOINT JAHAN DATA HAI ---
# Code mein dekha: fatchformno.php hi data deti hai
DATA_URL = "https://msbuexam.org/StSticTCntAlL/fatchformno.php"
REFERER_URL = "https://msbuexam.org/StSticTCntAlL/FindForm.php"

def get_msbu_data(name):
    # Cloudscraper to bypass Cloudflare
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    
    # Headers mein India ka Timezone mimic karna zaroori hai
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": REFERER_URL,
        "Origin": "https://msbuexam.org",
        "X-Requested-With": "XMLHttpRequest" # Website ko lagega AJAX request hai
    }
    
    try:
        # Website ke form fields ke naam code se uthaye hain: Sname, Fname, Mob, uid etc.
        payload = {
            'Sname': name,
            'Fname': '',
            'Mname': '',
            'Mob': '',
            'uid': '',
            'abc': '',
            'fno': '',
            'tzone': '5.5', # YE SABSE ZAROORI HAI (IST Bypass)
            'finfom': 'Proceed'
        }
        
        response = scraper.post(DATA_URL, data=payload, headers=headers, timeout=25)
        return response.text
    except:
        return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 **MSBU Multi-Search Bot Active!**\n\nBas Candidate ka Name bhejein.")

@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    search_name = message.text
    sent_msg = bot.reply_to(message, f"🔎 Searching for `{search_name}` (IST Bypass Mode)...")
    
    html_res = get_msbu_data(search_name)
    
    if not html_res:
        bot.edit_message_text("❌ Website ne response nahi diya.", message.chat.id, sent_msg.message_id)
        return

    # Response seedha table ya text ho sakta hai
    if "📝" in html_res or "Form" in html_res or "table" in html_res.lower():
        # BeautifulSoup use karke table parse karein
        soup = BeautifulSoup(html_res, 'html.parser')
        rows = soup.find_all('tr')
        
        if rows:
            res_msg = "✅ **Found Records:**\n\n"
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    res_msg += f"🆔 `{cols[0].text.strip()}` | 👤 {cols[1].text.strip()}\n"
            bot.edit_message_text(res_msg, message.chat.id, sent_msg.message_id)
        else:
            # Agar table nahi hai toh raw text bhej do (Jo fatchformno.php bhej rahi hai)
            bot.edit_message_text(f"✅ **Results:**\n\n{html_res}", message.chat.id, sent_msg.message_id)
    else:
        bot.edit_message_text("❌ Is naam ka koi record nahi mila.", message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
            
