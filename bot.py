import os
import telebot
import requests
from bs4 import BeautifulSoup

# TOKEN SECURITY: 
# Humne token code se hata diya hai. 
# Ab aapko Render/Koyeb ki settings mein 'BOT_TOKEN' naam ka variable banana hoga.
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

URL = "https://msbuexam.org/StSticTCntAlL/FindForm.php"

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "✅ **Registration Finder Bot Active!**\n\n"
        "Muje kisi ka bhi **Full Name** bhejo, main MSBU website se uski saari details nikal kar dunga."
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def search_handler(message):
    name_to_search = message.text
    bot.send_chat_action(message.chat.id, 'typing')
    sent_msg = bot.reply_to(message, f"🔍 `{name_to_search}` ki details nikal raha hoon...", parse_mode='Markdown')

    payload = {
        'txtSearch': name_to_search,
        'btnSearch': 'Search'
    }

    try:
        response = requests.post(URL, data=payload, timeout=20)
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
                    res_msg = (
                        f"📌 **Student Details Found:**\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"🆔 **Reg/Roll No:** `{data[0]}`\n"
                        f"👤 **Name:** {data[1]}\n"
                        f"👨‍💼 **Father's Name:** {data[2]}\n"
                        f"🎓 **Course:** {data[3] if len(data)>3 else 'N/A'}\n"
                        f"🏢 **College/Exam:** {data[4] if len(data)>4 else 'N/A'}\n"
                        f"━━━━━━━━━━━━━━━━━━\n\n"
                    )
                    all_results += res_msg

            if all_results:
                bot.edit_message_text(all_results, message.chat.id, sent_msg.message_id, parse_mode='Markdown')
            else:
                bot.edit_message_text("❌ Data process nahi ho paya.", message.chat.id, sent_msg.message_id)
        else:
            bot.edit_message_text("❌ Website response nahi de rahi.", message.chat.id, sent_msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"⚠️ Error: Connection failed.", message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    bot.polling(none_stop=True)
