import os, telebot, cloudscraper, urllib3
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread

# --- RENDER PORT LOGIC ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Active & Logging!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- BOT SETUP ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))

DATA_URL = "https://msbuexam.org/StSticTCntAlL/fatchformno.php"

def get_msbu_data(name):
    print(f"\n>>> [LOG] 1. New Request Received for Name: {name}")
    
    # Cloudscraper creates a browser-like session
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
    )
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://msbuexam.org/StSticTCntAlL/FindForm.php",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    payload = {
        'Sname': name, 'Fname': '', 'Mname': '', 'Mob': '',
        'uid': '', 'abc': '', 'fno': '', 'tzone': '5.5', 'finfom': 'Proceed'
    }

    try:
        print(">>> [LOG] 2. Sending POST request to MSBU Server...")
        
        # Yahan humne ek working proxy daalne ki jagah rakhi hai
        # Agar block hota hai toh yahan proxy add karni hogi
        response = scraper.post(DATA_URL, data=payload, headers=headers, timeout=25)
        
        print(f">>> [LOG] 3. Response Received. Status Code: {response.status_code}")
        print(f">>> [LOG] 4. HTML Data Length: {len(response.text)} characters")

        # Check for Cloudflare challenge
        if "cloudflare" in response.text.lower() or "Attention Required" in response.text:
            print(">>> [LOG] ALERT: Blocked by Cloudflare Firewall!")
            return "CF_BLOCKED"
            
        return response.text

    except Exception as e:
        print(f">>> [LOG] ERROR: Request failed due to: {str(e)}")
        return None

@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    search_name = message.text
    print(f"\n>>> [LOG] User {message.from_user.first_name} is searching: {search_name}")
    
    sent_msg = bot.reply_to(message, "🔎 Website se data nikaal raha hoon... (Checking Logs)")
    
    html = get_msbu_data(search_name)
    
    if html == "CF_BLOCKED":
        bot.edit_message_text("🚫 **Cloudflare Block:** Render ka IP block hai. Please Render ki settings mein jaakar **Region Change** karein.", message.chat.id, sent_msg.message_id)
    elif html:
        print(">>> [LOG] 5. Parsing HTML content...")
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        
        if table:
            rows = table.find_all('tr')
            print(f">>> [LOG] 6. Success! Found {len(rows)-1} records.")
            
            res = f"✅ **Records for {search_name}:**\n\n"
            for row in rows[1:]:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    res += f"📝 **Form:** `{cols[0].text.strip()}`\n👤 **Name:** {cols[1].text.strip()}\n👨‍💼 **Father:** {cols[2].text.strip()}\n━━━━━━━━━━━━\n"
            bot.edit_message_text(res, message.chat.id, sent_msg.message_id, parse_mode='Markdown')
        else:
            print(">>> [LOG] 6. Table NOT found in response. Possible 'No Record Found'.")
            bot.edit_message_text(f"❌ `{search_name}` ka koi record nahi mila.", message.chat.id, sent_msg.message_id)
    else:
        bot.edit_message_text("❌ Connection Error. Logs check karein.", message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    Thread(target=run).start()
    print(">>> [LOG] Bot is now Polling... Ready for messages.")
    bot.polling(none_stop=True)
    
