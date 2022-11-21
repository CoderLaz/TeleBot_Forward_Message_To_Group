import telebot
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')

bot = telebot.TeleBot(API_KEY, parse_mode=None)

@bot.message_handler(commands=['forward', 'start'])
def send_welcome(message):
    if message.text == '/start':
        bot.reply_to(message, "Dear User, Welcome to Text Forwarding Bot! Send '/forward' to begin using this bot..")
    bot.register_next_step_handler(message, send_message)


def send_message(message):
    msg = bot.reply_to(message, "Yo wassup I'm eager to know what you're looking to forward..")
    bot.register_next_step_handler(msg, forward)
    

def forward(message):
    chat_id = message.chat.id
    sender = message.from_user.username
    bot.send_message(-562184369, f'{message.text} (Sender: @{sender})')
    bot.send_message(chat_id, f'Hey @{message.from_user.username}, your message was forwarded to group: https://t.me/+XJQJ05w134gxODNl')

bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()

bot.infinity_polling()
