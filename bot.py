import os, telebot, cloudscraper, urllib3, time
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread

# --- RENDER PORT BINDING ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online & Accepting Cookies!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- BOT SETUP ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))

# Conflict 409 Fix
try:
    bot.remove_webhook()
    time.sleep(1)
except: pass

MAIN_URL = "https://msbuexam.org/StSticTCntAlL/FindForm.php"
DATA_URL = "https://msbuexam.org/StSticTCntAlL/fatchformno.php"

def get_msbu_data(name):
    # Ek session create kar rahe hain jo COOKIES yaad rakhega
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome','platform': 'windows','desktop': True}
    )
    
    print(f"\n>>> [LOG] STEP 1: Visiting Main Page to accept Cookies...")
    try:
        # Pehle main page par ja kar cookies accept karte hain
        init_res = scraper.get(MAIN_URL, timeout=15)
        print(f">>> [LOG] Cookies Accepted: {scraper.cookies.get_dict()}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": MAIN_URL,
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://msbuexam.org"
        }
        
        payload = {
            'Sname': name, 'Fname': '', 'Mname': '', 'Mob': '',
            'uid': '', 'abc': '', 'fno': '', 'tzone': '5.5', 'finfom': 'Proceed'
        }
        
        print(f">>> [LOG] STEP 2: Sending Search for: {name}")
        response = scraper.post(DATA_URL, data=payload, headers=headers, timeout=25)
        
        print(f">>> [LOG] STEP 3: Status: {response.status_code}, Length: {len(response.text)}")
        
        if "cloudflare" in response.text.lower() or "blocked" in response.text.lower():
            print(">>> [LOG] !!! Cloudflare Detected despite cookies")
            return "CF_BLOCK"
            
        return response.text

    except Exception as e:
        print(f">>> [LOG] !!! ERROR: {str(e)}")
        return None

@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    search_name = message.text
    print(f"\n>>> [LOG] USER {message.chat.id} triggered search.")
    
    sent_msg = bot.reply_to(message, "🍪 Accepting cookies & fetching data...")
    
    html = get_msbu_data(search_name)
    
    if html == "CF_BLOCK":
        bot.edit_message_text("🚫 Cloudflare is still blocking the IP. Check Render Logs!", message.chat.id, sent_msg.message_id)
    elif html:
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            print(f">>> [LOG] SUCCESS: Found {len(rows)-1} records.")
            res = f"✅ **Results for {search_name}:**\n\n"
            for row in rows[1:]:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    res += f"📝 **Form:** `{cols[0].text.strip()}`\n👤 **Name:** {cols[1].text.strip()}\n👨‍💼 **Father:** {cols[2].text.strip()}\n━━━━━━━━━━━━\n"
            bot.edit_message_text(res, message.chat.id, sent_msg.message_id)
        else:
            print(">>> [LOG] No table found. Website might have returned an empty response.")
            bot.edit_message_text(f"❌ `{search_name}` ka data nahi mila.", message.chat.id, sent_msg.message_id)
    else:
        bot.edit_message_text("❌ Request failed. Server issue.", message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    Thread(target=run).start()
    print(">>> [LOG] Bot is starting...")
    bot.polling(none_stop=True)
