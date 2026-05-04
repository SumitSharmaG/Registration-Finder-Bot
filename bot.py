import os
import telebot
import requests
from bs4 import BeautifulSoup
import urllib3

# SSL Warnings ko band karne ke liye
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

URL = "https://msbuexam.org/StSticTCntAlL/FindForm.php"

def get_data(name):
    # Ek session create karein taaki website ko lage ki hum bar-bar aa rahe hain
    session = requests.Session()
    
    # 403 Bypass karne ke liye updated Headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://msbuexam.org/StSticTCntAlL/FindForm.php",
        "Origin": "https://msbuexam.org",
        "Connection": "keep-alive"
    }

    try:
        # Step 1: Pehle page ko load karein (Cookies lene ke liye)
        session.get(URL, headers=headers, verify=False, timeout=15)

        # Step 2: Ab data post karein
        payload = {
            'candidateName': name,
            'fatherName': '',
            'submit': 'Search'
        }
        
        response = session.post(URL, data=payload, headers=headers, verify=False, timeout=20)
        return response
    except Exception as e:
        return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🛡️ **MSBU Finder (Anti-Block Mode) Active!**\n\nFull Name bhejo:")

@bot.message_handler(func=lambda message: True)
def search_handler(message):
    name_to_search = message.text
    sent_msg = bot.reply_to(message, f"⌛ `{name_to_search}` ko search kar raha hoon (Anti-403 Mode)...")

    response = get_data(name_to_search)

    if response is None:
        bot.edit_message_text("🚫 Connection Error! Website ne respond nahi kiya.", message.chat.id, sent_msg.message_id)
        return

    if response.status_code == 403:
        bot.edit_message_text("⚠️ Error 403: Website ne temporary block kiya hai. Kuch der baad try karein ya Father Name wala system lagayein.", message.chat.id, sent_msg.message_id)
        return

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        
        if table:
            rows = table.find_all('tr')
            if len(rows) <= 1:
                bot.edit_message_text("❌ Is naam se koi record nahi mila.", message.chat.id, sent_msg.message_id)
                return

            all_res = "✅ **Results Found:**\n\n"
            for row in rows[1:6]:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    all_res += f"🆔 `{cols[0].text.strip()}` | 👤 {cols[1].text.strip()}\n"
            
            bot.edit_message_text(all_res, message.chat.id, sent_msg.message_id)
        else:
            bot.edit_message_text("⚠️ Website ne table nahi dikhaya. Shayad Father Name bhi zaroori hai.", message.chat.id, sent_msg.message_id)
    else:
        bot.edit_message_text(f"❌ Site Error: {response.status_code}", message.chat.id, sent_msg.message_id)

bot.polling(none_stop=True)
        
