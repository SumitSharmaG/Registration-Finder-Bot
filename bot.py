import os, telebot, cloudscraper, urllib3, requests
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread

# --- RENDER PORT BINDING ---
app = Flask('')
@app.route('/')
def home(): return "Proxy Bypass Bot is Running!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- CORE LOGIC ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))

def get_msbu_data(name):
    # Cloudscraper logic with custom browser fingerprint
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'android', 'desktop': False}
    )
    
    url = "https://msbuexam.org/StSticTCntAlL/fatchformno.php"
    headers = {
        "Referer": "https://msbuexam.org/StSticTCntAlL/FindForm.php",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://msbuexam.org"
    }
    
    payload = {
        'Sname': name, 'Fname': '', 'Mname': '', 'Mob': '',
        'uid': '', 'abc': '', 'fno': '', 'tzone': '5.5', 'finfom': 'Proceed'
    }

    try:
        # Pehle bina proxy ke koshish (Mobile Fingerprint ke saath)
        response = scraper.post(url, data=payload, headers=headers, timeout=20)
        
        # Agar Cloudflare block karega toh hum ek public proxy try karenge
        if "cloudflare" in response.text.lower() or response.status_code == 403:
            print(">>> [LOG] Blocked by CF. Trying Public Proxy...")
            
            # Ye ek demo proxy hai (Bhai, ye kabhi bhi dead ho sakti hai)
            # Aap 'https://www.sslproxies.org/' se naya IP lekar yahan badal sakte ho
            test_proxy = "http://160.86.242.23:8080" 
            proxies = {"http": test_proxy, "https": test_proxy}
            
            response = scraper.post(url, data=payload, headers=headers, proxies=proxies, timeout=20)
            
        return response.text
    except Exception as e:
        return f"ERROR: {str(e)}"

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 **MSBU Ultimate Bypass Bot**\n\nStudent ka naam bhejein. Main Cloudflare aur IP block se ladne ki koshish karunga!")

@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    search_name = message.text
    sent_msg = bot.reply_to(message, "🛡️ **Security Bypass in Progress...**")
    
    html = get_msbu_data(search_name)
    
    if not html or "cloudflare" in html.lower():
        bot.edit_message_text("🚫 **Still Blocked:** Cloudflare ne Render ka pura network block kar rakha hai. Render ki Settings mein jaakar **Region change** karein (Singapore ya Frankfurt).", message.chat.id, sent_msg.message_id)
        return

    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    
    if table:
        rows = table.find_all('tr')
        res = f"✅ **Records for {search_name}:**\n\n"
        for row in rows[1:]:
            cols = row.find_all('td')
            if len(cols) >= 3:
                res += f"🆔 `{cols[0].text.strip()}` | 👤 {cols[1].text.strip()}\n"
        bot.edit_message_text(res, message.chat.id, sent_msg.message_id)
    else:
        bot.edit_message_text("❌ Record nahi mila ya site down hai.", message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    Thread(target=run).start()
    bot.polling(none_stop=True)
