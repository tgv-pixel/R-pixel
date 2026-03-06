#!/usr/bin/env python3
# app.py - Telegram Bot with Flask Webhook

import os
import logging
from flask import Flask, request
import telegram
from telegram.ext import Dispatcher, CommandHandler, CallbackContext, MessageHandler, Filters

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

# Initialize bot
bot = telegram.Bot(token=BOT_TOKEN)

# Create dispatcher
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# ==================== COMMAND HANDLERS ====================

def start(update, context):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_text(
        f"👋 Hi {user.first_name}!\n\n"
        f"Welcome to the Dating Bot!\n"
        f"Use /help to see available commands."
    )

def help_command(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/menu - Show main menu\n"
        "/status - Check bot status"
    )

def menu_command(update, context):
    """Show main menu"""
    keyboard = [
        [telegram.InlineKeyboardButton("💕 Find Partner", callback_data='find_partner')],
        [telegram.InlineKeyboardButton("🇪🇹 አማርኛ", callback_data='lang_am')],
        [telegram.InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')],
    ]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Main Menu:", reply_markup=reply_markup)

def status_command(update, context):
    """Check bot status"""
    update.message.reply_text("✅ Bot is running on Render!")

def button_handler(update, context):
    """Handle button presses"""
    query = update.callback_query
    query.answer()
    
    data = query.data
    
    if data == 'find_partner':
        query.edit_message_text("Finding partners feature coming soon!")
    elif data == 'lang_am':
        query.edit_message_text("🇪🇹 አማርኛ ተመርጧል")
    elif data == 'lang_en':
        query.edit_message_text("🇬🇧 English selected")

def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(f"You said: {update.message.text}")

# ==================== REGISTER HANDLERS ====================

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(CommandHandler("menu", menu_command))
dispatcher.add_handler(CommandHandler("status", status_command))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
dispatcher.add_handler(telegram.ext.CallbackQueryHandler(button_handler))

# ==================== FLASK ROUTES ====================

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming Telegram updates"""
    if request.method == 'POST':
        try:
            update = telegram.Update.de_json(request.get_json(force=True), bot)
            dispatcher.process_update(update)
        except Exception as e:
            logger.error(f"Error processing update: {e}")
        return 'OK', 200
    return 'OK', 200

@app.route('/')
def index():
    return "🤖 Telegram Dating Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

# ==================== MAIN ====================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
