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
    groups = db.Column(db.String)
    # aaifl = auth and in_forwarding_loop, group name {username: [False, [False, Group]],}
    aaifl = db.Column(db.String)
    created = db.Column(db.String(24), nullable=False)
    updated = db.Column(db.String(24), nullable=False)


def create_config():
    try:
        # checking if row already exists or else creating and adding new row
        if not Config.query.filter_by(sno=1).first():
            pwd = '12345678'
            groups = {'Forwarded Messages From @text_forwarding_bot': -562184369, 'second': -12345678, 'third': -12345678}
            created = updated = get_datetime()
            config = Config(pwd=generate_password_hash(pwd), groups=str(groups), aaifl='{}', created=created, updated=updated)
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


# Manually setting in_forward_loop to false during testing phase
# config = Config.query.filter_by(sno=1).first()
# aaifl = ast.literal_eval(config.aaifl)
# aaifl['pro_laz'][1][0] = False
# config.aaifl = str(aaifl)
# db.session.add(config)
# db.session.commit()
# print('committed')


bot = telebot.TeleBot(API_KEY, parse_mode=None)

# string of dictionary from row is converted to dictionary using ast.literal_eval()
groups_keys = ast.literal_eval(Config.query.filter_by(sno=1).first().groups).keys()
groups = "Please enter the group's serial number you want the message to be forwarded:\n"
group_sno = 0
for group in groups_keys:
    group_sno += 1
    groups += f'{group_sno}. {group}\n\n'


@bot.message_handler(commands=['forward', 'start'])
def greet(message):
    # print('inside greet')
    global username
    global aaifl
    global config
    

    config = Config.query.filter_by(sno=1).first()
    aaifl = ast.literal_eval(config.aaifl)
    username = message.from_user.username
    
    if username in aaifl and aaifl[username][0]:
        if aaifl[username][1][0]:
            # print('forward called from greet')
            bot.register_next_step_handler(message, forward)
        else:
            # print('context called from greet')
            msg = bot.reply_to(message, groups)
            bot.register_next_step_handler(msg, context)
    elif message.text == '/start':
        bot.send_message(f'Hi @{username}, Confirm password to begin using this bot..')
        bot.register_next_step_handler(message, validate)


def validate(message):
    # print('inside validate')
    text = message.text
    
    if check_password_hash(config.pwd, text):
        aaifl[username] = []
        l = aaifl[username]
        l.append(True)
        l.append([False, list(groups_keys)[0]])
        Config.query.filter_by(sno=1).first().aaifl = str(aaifl)
        db.session.add(Config.query.filter_by(sno=1).first())
        db.session.commit()
        
        # print('context called from validate')
        msg = bot.reply_to(message, groups)
        bot.register_next_step_handler(msg, context)
    else:
        msg = bot.reply_to(message, 'Incorrect Password! Try Again!!')


def context(message):
    # print('inside context')
    global group_name
    group_sno = message.text
    try:
        group_sno = int(group_sno)
        group_name = list(groups_keys)[group_sno - 1]
        if group_sno in [i + 1 for i in range(len(groups_keys))]:
            Config.query.filter_by(sno=1).first().aaifl = str(aaifl)
            aaifl[username][1][1] = list(groups_keys)[group_sno - 1]
            db.session.add(Config.query.filter_by(sno=1).first())
            db.session.commit()
            
            # print('forward called from context')
            msg = bot.reply_to(message, f"Please confirm the messages you want to send: (Enter '/quit' to exit)")
            bot.register_next_step_handler(msg, forward)
        else:
            bot.reply_to(message, f"Group {message.text} doesn't exist! Try Again!!")
    except:
        bot.reply_to(message, f"Group {message.text} doesn't exist! Try Again!!")


def forward(message):
    # print('inside forward')
    chat_id = message.chat.id
    config = Config.query.filter_by(sno=1).first()
    aaifl = ast.literal_eval(config.aaifl)
    if message.text == '/quit':
        # print('stopped')

        aaifl[username][1][0] = False
        config.aaifl = str(aaifl)
        db.session.add(config)
        db.session.commit()
        
        bot.send_message(chat_id, f"Stopped forwarding messages.. Restart the bot with '/start'...")
        bot.register_next_step_handler(message, context)
    elif message.text == '/start':
        # print('stopped')

        aaifl[username][1][0] = False
        config.aaifl = str(aaifl)
        db.session.add(config)
        db.session.commit()

        message = bot.reply_to(message, groups)
        bot.register_next_step_handler(message, context)
    else:
        aaifl[username][1][0] = True
        config.aaifl = str(aaifl)
        db.session.add(config)
        db.session.commit()

        # print('forwarded')

        bot.send_message(ast.literal_eval(config.groups)[aaifl[username][1][1]], f'{message.text}')
        bot.send_message(chat_id, f"Hey @{username}, your message was forwarded.")
        message = bot.send_message(chat_id, f"Please confirm the messages you want to send: (Enter '/quit' to exit)")
        bot.register_next_step_handler(message, forward)

bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()

bot.infinity_polling()
