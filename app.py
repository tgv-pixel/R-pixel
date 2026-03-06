#!/usr/bin/env python3
# app.py - Minimal Test Bot for Render

import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, CallbackContext

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN environment variable set!")

# Initialize Flask app
app = Flask(__name__)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# Simple command handlers
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🤖 Bot is working!\n\n"
        "Send /help to see commands"
    )

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/status - Check bot status"
    )

def status(update: Update, context: CallbackContext):
    update.message.reply_text("✅ Bot is running on Render!")

# Add handlers to dispatcher
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(CommandHandler("status", status))

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming Telegram updates"""
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'OK', 200

@app.route('/')
def index():
    return "🤖 Telegram Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
