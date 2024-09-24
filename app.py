from flask import Flask
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import threading

app = Flask(__name__)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "7948724735:AAFfOHaUkFTFEOr4w3VxXoHPHNiM_0NTXO"
bot = Bot(token=TOKEN)

updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

user_activity = {}

def track_activity(update: Update, context):
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    
    if chat_id not in user_activity:
        user_activity[chat_id] = {}
    
    user_activity[chat_id][user_id] = datetime.now()

def remove_inactive_users():
    threshold_date = datetime.now() - timedelta(days=30)
    
    for chat_id, users in list(user_activity.items()):
        for user_id, last_active in list(users.items()):
            if last_active < threshold_date:
                try:
                    bot.kick_chat_member(chat_id, user_id)
                    del user_activity[chat_id][user_id]
                    logger.info(f"User {user_id} was removed from chat {chat_id} due to inactivity.")
                except Exception as e:
                    logger.error(f"Failed to kick user {user_id} from chat {chat_id}: {e}")

def schedule_removal():
    scheduler = BackgroundScheduler()
    scheduler.add_job(remove_inactive_users, 'cron', day=1, hour=0)
    scheduler.start()

dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, track_activity))

def run_bot():
    updater.start_polling()
    updater.idle()

@app.route('/ping', methods=['GET'])
def ping():
    return "Pong!", 200

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    schedule_removal()

    app.run(host='0.0.0.0', port=5000)
