from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime
import pytz

import os
from dotenv import load_dotenv

import ast

import telebot

load_dotenv()

# confidential keys
DB_NAME = os.getenv('DB_NAME')
SECRET_KEY = os.getenv('SECRET_KEY')
API_KEY = os.getenv('API_KEY')

# using flask for maintaining sqlite db through sqlalchemy orm
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# secret key generated with help of uuid4 in order to make it most unique
app.config['SECRET_KEY'] = f'{SECRET_KEY}'

db = SQLAlchemy(app)

def get_datetime():
    return datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%d %b %Y %I:%M:%S %p")

# database model
class Config(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    pwd = db.Column(db.String(24), nullable=False)
    groups = db.Column(db.String)
    created = db.Column(db.String(24), nullable=False)
    updated = db.Column(db.String(24), nullable=False)


def create_config():
    try:
        # checking if row already exists or else creating and adding new row
        if not Config.query.filter_by(sno=1).first():
            pwd = '12345678'
            groups = {'Forwarded Messages From @text_forwarding_bot': -562184369, 'second': -12345678, 'third': -12345678}
            created = updated = get_datetime()
            config = Config(pwd=generate_password_hash(pwd), groups=str(groups), created=created, updated=updated)
            db.session.add(config)
            db.session.commit()
            print('SUCCESS: Database created successfully!')
    except:
        print('ERROR: Database already exists!')


try:
    if len(Config.query.all()) != 1:
        pass
except Exception as e:
        db.create_all()
        create_config()


bot = telebot.TeleBot(API_KEY, parse_mode=None)
# print([i + 1 for i in range(len(ast.literal_eval(Config.query.filter_by(sno=1).first().groups).keys()))])
@bot.message_handler(commands=['forward', 'start'])
def greet(message):
    if message.text == '/start':
        bot.reply_to(message, 'Dear User, Welcome to Text Forwarding Bot! Confirm password to begin using this bot..')
    bot.register_next_step_handler(message, validate)


def validate(message):
    pwd = message.text
    groups = "Please enter the group's serial number you want the message to be forwarded:\n"
    global groups_list, config
    config = Config.query.filter_by(sno=1).first()
    
    # string of dictionary from row is converted to dictionary using ast.literal_eval()
    groups_list = ast.literal_eval(config.groups).keys()
    
    group_sno = 0
    for group in groups_list:
        group_sno += 1
        groups += f'{group_sno}. {group}\n\n'
    
    if check_password_hash(config.pwd, pwd):
        msg = bot.reply_to(message, groups)
        bot.register_next_step_handler(msg, context)
    else:
        msg = bot.reply_to(message, 'Incorrect Password! Try Again!!')


def context(message):
    global group_name
    group_sno = message.text
    try:
        group_sno = int(group_sno)
        group_name = list(groups_list)[group_sno - 1]
        if group_sno in [i + 1 for i in range(len(groups_list))]:
            msg = bot.reply_to(message, f'Please confirm the message you want to send to group {message.text}:')
            bot.register_next_step_handler(msg, forward)
        else:
            bot.reply_to(message, f"Group {message.text} doesn't exist! Try Again!!")
    except:
        bot.reply_to(message, f"Group {message.text} doesn't exist! Try Again!!")


def forward(message):
    chat_id = message.chat.id
    sender = message.from_user.username
    bot.send_message(-562184369, f'{message.text}')
    bot.send_message(chat_id, f"Dear @{sender}, your message was forwarded to group '{group_name}'")

bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()

bot.infinity_polling()
