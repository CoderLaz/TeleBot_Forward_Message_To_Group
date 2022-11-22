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
PWD = os.getenv('PWD')

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
    # auth = auth and in_forwarding_loop, group name {username: False,}
    auth = db.Column(db.String)
    created = db.Column(db.String(24), nullable=False)
    updated = db.Column(db.String(24), nullable=False)


def create_config():
    try:
        # checking if row already exists or else creating and adding new row
        if not Config.query.filter_by(sno=1).first():
            pwd = PWD
            created = updated = get_datetime()
            config = Config(pwd=generate_password_hash(pwd), auth='{}', created=created, updated=updated)
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

@bot.message_handler(commands=['forward', 'start'])
def greet(message):
    global username
    global auth
    global config
    
    config = Config.query.filter_by(sno=1).first()
    auth = ast.literal_eval(config.auth)
    username = message.from_user.username

    # print(config.auth)
    if username in auth and username != 'None' and auth[username]:
        msg = bot.reply_to(message, 'Please send the signals now:')
        bot.register_next_step_handler(msg, forward)
    elif message.text == '/start':
        if username == 'None':
            bot.reply_to(message, f'Hi, Your username is None, Please set your username and try again!')
        else:
            bot.reply_to(message, f'Hi @{username}, Confirm password to begin using this bot..')
            bot.register_next_step_handler(message, validate)


def validate(message):
    # print('inside validate')
    text = message.text
    
    if check_password_hash(Config.query.filter_by(sno=1).first().pwd, text):
        auth[username] = []
        l = auth[username]
        l.append(True)
        Config.query.filter_by(sno=1).first().auth = str(auth)
        db.session.add(Config.query.filter_by(sno=1).first())
        db.session.commit()
        
        # print('forward called from validate')
        msg = bot.reply_to(message, 'Password verification is successful ✅\n\nPlease send the signals now:')
        bot.register_next_step_handler(msg, forward)
    else:
        msg = bot.reply_to(message, 'Incorrect Password! Try Again!!')


def forward(message):
    # print('inside forward')
    chat_id = message.chat.id
    # print('forwarded')

    bot.send_message(-562184369, f'{message.text}')
    bot.send_message(chat_id, f"Hey @{username}, your message was forwarded.")
    message = bot.send_message(chat_id, f"Please send the signals now:")
    bot.register_next_step_handler(message, forward)


bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()

bot.infinity_polling()
