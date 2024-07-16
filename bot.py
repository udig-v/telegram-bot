import os
import json
import random
import requests
from flask import Flask, request, Response
from typing import final
from dotenv import load_dotenv, dotenv_values
from datetime import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

app = Flask(__name__)

load_dotenv()

BOT_KEY: final = os.getenv("TELEGRAM_BOT_KEY")
BOT_USERNAME: final = "HiMyNameIsBobBot"
DATA_FILE = "quotes.json"

with open("quotes.json", "r", encoding="utf-8") as file:
    quotes = json.load(file)


def get_random_quote() -> str:
    quote = random.choice(quotes)
    return f"{quote['quote']}"


def save_data(data: dict):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)


# Routes
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        msg = request.get_json()
        print(msg)
        chat_id = message_parser(msg)
        send_message(chat_id, "Hello! You will receive daily quotes.")
        return Response(response="OK", status=200)
    else:
        return "<h1>Something went wrong</h1>"


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_KEY}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    response = requests.post(url, payload)
    return response


def message_parser(msg):
    chat_id = msg["message"]["chat"]["id"]
    text = msg["message"]["text"]
    print(f"Chat ID: {chat_id}, Text: {text}")
    return chat_id


# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! You will receive daily quotes.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Use /start to start the bot, /add to log food, /list to see what you've logged."
    )


async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quote = get_random_quote()
    await update.message.reply_text(quote)


async def send_daily_quote(context: ContextTypes.DEFAULT_TYPE):
    for user_id in context.bot_data.get("subscribed_users", []):
        quote = get_random_quote()
        await context.bot.send_message(chat_id=user_id, text=quote)


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id: int = update.message.from_user.id
    subscribed_users = context.bot_data.setdefault("subscribed_users", [])
    if user_id not in subscribed_users:
        subscribed_users.append(user_id)
        await update.message.reply_text("You have subscribed to daily Quran quotes.")
    else:
        await update.message.reply_text("You are already subscribed.")


async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    subscribed_users = context.bot_data.setdefault("subscribed_users", [])
    if user_id in subscribed_users:
        subscribed_users.remove(user_id)
        await update.message.reply_text(
            "You have unsubscribed from daily Quran quotes."
        )
    else:
        await update.message.reply_text("You are not subscribed.")


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {Update} caused error {context.error}")


if __name__ == "__main__":
    print("Starting bot...")
    app.run(host="0.0.0.0", debug=False, port=int(os.environ.get("PORT", 5000)))

    app = Application.builder().token(BOT_KEY).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("quote", quote_command))
    app.add_handler(CommandHandler("subscribe", subscribe_command))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe_command))

    scheduler = BackgroundScheduler()
    scheduler.add_job(send_daily_quote, CronTrigger(hour=8, minute=0), args=[app.bot])
    scheduler.start()

    # Error
    app.add_error_handler(error)

    # Polls the bot
    print("Polling...")
    app.run_polling()
