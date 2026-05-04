import os
import telebot
import requests
from bs4 import BeautifulSoup

# Render ki settings se Token uthayega
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

URL = "https://msbuexam.org/StSticTCntAlL/FindForm.php"

# Browser ki nakli identity taaki website block na kare
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Origin": "https://msbuexam.org",
    "Referer": "https://msbuexam.org/StSticTCntAlL/FindForm.php"
}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ **Registration Finder Active!**\n\nFull Name bhejo (Example: Sumit Kumar Sharma)")

@bot.message_handler(func=lambda message: True)
def search_handler(message):
    name_to_search = message.text
    sent_msg = bot.reply_to(message, f"🔍 `{name_to_search}` ko search kar raha hoon...")

    # Ye fields website ke form ke hisab se hain
    payload = {
        'candidateName': name_to_search, 
        'submit': 'Search'
    }

    try:
        # Website se data mangna
        response = requests.post(URL, data=payload, headers=HEADERS, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table')
            
            if table:
                rows = table.find_all('tr')
                if len(rows) <= 1:
                    bot.edit_message_text("❌ Is naam se koi record nahi mila.", message.chat.id, sent_msg.message_id)
                    return

                all_results = ""
                for row in rows[1:6]:
                    cols = row.find_all('td')
                    data = [ele.text.strip() for ele in cols]
                    if len(data) >= 3:
                        all_results += f"🆔 **Reg No:** `{data[0]}`\n👤 **Name:** {data[1]}\n👨‍💼 **Father:** {data[2]}\n━━━━━━━━━━━━\n\n"
                
                bot.edit_message_text(all_results, message.chat.id, sent_msg.message_id, parse_mode='Markdown')
            else:
                bot.edit_message_text("⚠️ Website ne data table nahi dikhaya. Shayad server down hai.", message.chat.id, sent_msg.message_id)
        else:
            bot.edit_message_text(f"❌ Website Error: {response.status_code}", message.chat.id, sent_msg.message_id)

    except Exception as e:
        bot.edit_message_text("🚫 Connection Timeout! Dobara try karein.", message.chat.id, sent_msg.message_id)

bot.polling(none_stop=True)
            
