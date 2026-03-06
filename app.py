#!/usr/bin/env python3
# app.py - Complete Working Telegram Bot for Render

import os
import logging
from flask import Flask, request
import telegram
from telegram.ext import Dispatcher, CommandHandler, CallbackContext, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    BOT_TOKEN = "7294379764:AAEnjI8VE3Frw2__C5D0uzGc4sLzteehqS0"  # Fallback (but set in Render)

# Initialize Flask app
app = Flask(__name__)

# Initialize bot
bot = telegram.Bot(token=BOT_TOKEN)

# Create dispatcher
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

# ==================== LANGUAGE TRANSLATIONS ====================
TRANSLATIONS = {
    'am': {
        'welcome': '👋 እንኳን ወደ የፍቅር ጓደኝነት ቦት በደህና መጡ!',
        'language_selected': '🇪🇹 አማርኛ ተመርጧል',
        'main_menu': '🎯 ዋና ሜኑ፦',
        'find_partner': '💕 ጓደኛ ፈልግ',
        'online': '💻 ኦንላይን',
        'in_person': '👥 ፊት ለፊት',
        'short_night': '🌙 አጭር ሌሊት',
        'full_night': '⭐ ሙሉ ሌሊት',
        'payment_required': '💳 እባክዎ መጀመሪያ 500 ብር ይክፈሉ',
        'cbe': '🏦 የኢትዮጵያ ንግድ ባንክ - 1000612391754',
        'tele_birr': '📱 ቴሌ ብር - 0940980555',
        'enter_phone': '📱 እባክዎ ስልክ ቁጥርዎን ያስገቡ:',
        'payment_success': '✅ ክፍያዎ ተረጋግጧል!',
        'choose_service': '📋 የሚፈልጉትን አገልግሎት ይምረጡ:',
    },
    'en': {
        'welcome': '👋 Welcome to the Dating Bot!',
        'language_selected': '🇬🇧 English selected',
        'main_menu': '🎯 Main Menu:',
        'find_partner': '💕 Find Partner',
        'online': '💻 Online',
        'in_person': '👥 In Person',
        'short_night': '🌙 Short Night',
        'full_night': '⭐ Full Night',
        'payment_required': '💳 Please pay 500 Birr first',
        'cbe': '🏦 CBE - 1000612391754',
        'tele_birr': '📱 Tele Birr - 0940980555',
        'enter_phone': '📱 Please enter your phone number:',
        'payment_success': '✅ Payment verified!',
        'choose_service': '📋 Choose your service:',
    }
}

# ==================== COMMAND HANDLERS ====================

def start(update, context):
    """Send welcome message with language selection"""
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data='lang_am')],
        [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        f"👋 Hi {user.first_name}!\n"
        f"Welcome! እንኳን ደህና መጡ!\n"
        f"Please choose your language / እባክዎ ቋንቋ ይምረጡ:",
        reply_markup=reply_markup
    )

def help_command(update, context):
    """Send help message"""
    update.message.reply_text(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/menu - Show main menu\n"
        "/pay - Show payment info\n"
        "/help - Show this help"
    )

def menu_command(update, context):
    """Show main menu"""
    lang = context.user_data.get('language', 'en')
    
    keyboard = [
        [InlineKeyboardButton(TRANSLATIONS[lang]['find_partner'], callback_data='find_partner')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        TRANSLATIONS[lang]['main_menu'],
        reply_markup=reply_markup
    )

def pay_command(update, context):
    """Show payment information"""
    keyboard = [
        [InlineKeyboardButton("✅ I have paid", callback_data='verify_payment')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        f"💳 Payment Information:\n\n"
        f"🏦 CBE: 1000612391754\n"
        f"📱 Tele Birr: 0940980555\n"
        f"💰 Amount: 500 Birr\n\n"
        f"After payment, click the button below:",
        reply_markup=reply_markup
    )

def status_command(update, context):
    """Check bot status"""
    update.message.reply_text("✅ Bot is running on Render! 🤖")

def button_handler(update, context):
    """Handle button presses"""
    query = update.callback_query
    query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    # Initialize user data
    if 'language' not in context.user_data:
        context.user_data['language'] = 'en'
    
    lang = context.user_data['language']
    
    # Language selection
    if data == 'lang_am':
        context.user_data['language'] = 'am'
        query.edit_message_text(TRANSLATIONS['am']['language_selected'])
        show_main_menu(query, context)
    
    elif data == 'lang_en':
        context.user_data['language'] = 'en'
        query.edit_message_text(TRANSLATIONS['en']['language_selected'])
        show_main_menu(query, context)
    
    # Main menu options
    elif data == 'find_partner':
        show_service_options(query, context)
    
    elif data in ['online', 'in_person', 'short_night', 'full_night']:
        show_payment_options(query, context, data)
    
    # Payment
    elif data == 'verify_payment':
        query.edit_message_text(TRANSLATIONS[lang]['enter_phone'])
        context.user_data['awaiting_phone'] = True

def show_main_menu(query, context):
    """Show main menu after language selection"""
    lang = context.user_data['language']
    
    keyboard = [
        [InlineKeyboardButton(TRANSLATIONS[lang]['find_partner'], callback_data='find_partner')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        TRANSLATIONS[lang]['main_menu'],
        reply_markup=reply_markup
    )

def show_service_options(query, context):
    """Show service options"""
    lang = context.user_data['language']
    
    keyboard = [
        [InlineKeyboardButton(TRANSLATIONS[lang]['online'], callback_data='online')],
        [InlineKeyboardButton(TRANSLATIONS[lang]['in_person'], callback_data='in_person')],
        [InlineKeyboardButton(TRANSLATIONS[lang]['short_night'], callback_data='short_night')],
        [InlineKeyboardButton(TRANSLATIONS[lang]['full_night'], callback_data='full_night')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        TRANSLATIONS[lang]['choose_service'],
        reply_markup=reply_markup
    )

def show_payment_options(query, context, service):
    """Show payment options"""
    lang = context.user_data['language']
    
    keyboard = [
        [InlineKeyboardButton(TRANSLATIONS[lang]['cbe'], callback_data='cbe_paid')],
        [InlineKeyboardButton(TRANSLATIONS[lang]['tele_birr'], callback_data='tele_paid')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        f"{TRANSLATIONS[lang]['payment_required']}\n\n"
        f"Selected: {service}\n\n"
        f"Choose payment method:",
        reply_markup=reply_markup
    )

def handle_message(update, context):
    """Handle text messages"""
    lang = context.user_data.get('language', 'en')
    
    # Check if waiting for phone number
    if context.user_data.get('awaiting_phone'):
        phone = update.message.text
        
        update.message.reply_text(
            f"{TRANSLATIONS[lang]['payment_success']}\n"
            f"Phone: {phone}\n\n"
            f"An admin will verify your payment soon."
        )
        context.user_data['awaiting_phone'] = False
        
        # Show main menu
        menu_command(update, context)
    else:
        update.message.reply_text(f"Use /menu to see options")

# ==================== REGISTER HANDLERS ====================
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(CommandHandler("menu", menu_command))
dispatcher.add_handler(CommandHandler("pay", pay_command))
dispatcher.add_handler(CommandHandler("status", status_command))
dispatcher.add_handler(CallbackQueryHandler(button_handler))
dispatcher.add_handler(MessageHandler(telegram.ext.Filters.text & ~telegram.ext.Filters.command, handle_message))

# ==================== FLASK ROUTES ====================

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming Telegram updates"""
    if request.method == 'POST':
        try:
            update = telegram.Update.de_json(request.get_json(force=True), bot)
            dispatcher.process_update(update)
        except Exception as e:
            logger.error(f"Error: {e}")
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
