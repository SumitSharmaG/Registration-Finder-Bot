import os, telebot, requests, urllib3
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread

# --- RENDER PORT FIX (Do not remove) ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive and Running!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ---------------------------------------

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))
URL = "https://msbuexam.org/StSticTCntAlL/FindForm.php"

def get_msbu_data(name):
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": URL,
        "Origin": "https://msbuexam.org"
    }
    try:
        # Step 1: Initial visit for cookies
        session.get(URL, headers=headers, verify=False, timeout=10)
        
        # Step 2: Search with Candidate Name (Multiple results supported)
        payload = {
            'candidateName': name,
            'fatherName': '', # Single box entry as requested
            'submit': 'Search'
        }
        response = session.post(URL, data=payload, headers=headers, verify=False, timeout=25)
        return response.text
    except:
        return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 **MSBU Student Finder Active!**\n\nSirf Student ka Name bhejein, main saari details (Single/Multiple) nikaal loonga!")

@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    search_name = message.text
    sent_msg = bot.reply_to(message, f"🔎 `{search_name}` ke records dhoond raha hoon...")
    
    html = get_msbu_data(search_name)
    if not html:
        bot.edit_message_text("❌ Website response nahi de rahi. Thodi der baad try karein.", message.chat.id, sent_msg.message_id)
        return

    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table') # MSBU data hamesha table mein hota hai
    
    if table:
        rows = table.find_all('tr')
        # rows[0] header hoti hai, results rows[1] se shuru hote hain
        if len(rows) > 1:
            total_found = len(rows) - 1
            results = f"✅ **Total {total_found} Students Found:**\n\n"
            
            for row in rows[1:]:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    results += (
                        f"📝 **Form:** `{cols[0].text.strip()}`\n"
                        f"👤 **Name:** {cols[1].text.strip()}\n"
                        f"👨‍💼 **Father:** {cols[2].text.strip()}\n"
                        f"━━━━━━━━━━━━\n"
                    )
                # Telegram message limit safety
                if len(results) > 3800:
                    results += "\n⚠️ *List bahut lambi hai, sirf shuruat ke dikha raha hoon.*"
                    break
                    
            bot.edit_message_text(results, message.chat.id, sent_msg.message_id, parse_mode='Markdown')
        else:
            bot.edit_message_text("❌ Is naam ka koi record nahi mila.", message.chat.id, sent_msg.message_id)
    else:
        bot.edit_message_text("⚠️ Site layout changed ya data nahi mila. Ek baar manually site check karein.", message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    keep_alive() # Render stay-alive logic
    print("Bot starting...")
    bot.polling(none_stop=True)
