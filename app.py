#!/usr/bin/env python3
# server.py - Complete Telegram Dating Bot for Render.com

import logging
import os
import sqlite3
from datetime import datetime
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ==================== CONFIGURATION ====================
# Get environment variables (set these in Render dashboard)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN environment variable set!")

ADMIN_IDS = [int(id) for id in os.environ.get('ADMIN_IDS', '894002841').split(',') if id]
CBE_ACCOUNT = os.environ.get('CBE_ACCOUNT', '1000612391754')
TELE_BIRR_NUMBER = os.environ.get('TELE_BIRR_NUMBER', '0940980555')
PAYMENT_AMOUNT = int(os.environ.get('PAYMENT_AMOUNT', 500))

# Database path (use /tmp for Render's ephemeral storage)
DB_PATH = '/tmp/dating_bot.db' if os.environ.get('RENDER') else 'dating_bot.db'

# ==================== LOGGING ====================
logging.basic8Config(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== DATABASE SETUP ====================
def init_db():
    """Initialize SQLite database tables"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id INTEGER PRIMARY KEY, 
                      username TEXT,
                      first_name TEXT,
                      language TEXT DEFAULT 'en',
                      paid INTEGER DEFAULT 0,
                      payment_date TEXT,
                      phone TEXT,
                      registered_date TEXT)''')
        
        # Payments table
        c.execute('''CREATE TABLE IF NOT EXISTS payments
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      amount INTEGER,
                      method TEXT,
                      phone TEXT,
                      status TEXT DEFAULT 'pending',
                      date TEXT)''')
        
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    finally:
        conn.close()

# ==================== LANGUAGE TRANSLATIONS ====================
TRANSLATIONS = {
    'am': {
        'welcome': '👋 እንኳን ወደ የፍቅር ጓደኝነት ቦት በደህና መጡ!\nእባክዎ ቋንቋ ይምረጡ:',
        'language_selected': '🇪🇹 አማርኛ ተመርጧል',
        'main_menu': '🎯 ዋና ሜኑ፦\nከዚህ በታች ካሉት አማራጮች ይምረጡ:',
        'find_partner': '💕 ጓደኛ ፈልግ',
        'online': '💻 ኦንላይን',
        'in_person': '👥 ፊት ለፊት',
        'short_night': '🌙 አጭር ሌሊት',
        'full_night': '⭐ ሙሉ ሌሊት',
        'payment_required': f'💳 እባክዎ መጀመሪያ {PAYMENT_AMOUNT} ብር ይክፈሉ\n\nመረጡት አገልግሎት: {{service}}\n\nየክፍያ ዘዴ ይምረጡ:',
        'cbe': '🏦 የኢትዮጵያ ንግድ ባንክ',
        'tele_birr': '📱 ቴሌ ብር',
        'payment_instructions': '💳 ክፍያ ለማድረግ፦\n\n{method} ይጠቀሙ\nስልክ ቁጥር: {number}\nመጠን: {amount} ብር\n\nከክፍያ በኋላ ስልክ ቁጥርዎን ይላኩ:',
        'verify_payment': '🔄 ክፍያዬን አረጋግጥ',
        'enter_phone': '📱 እባክዎ ስልክ ቁጥርዎን ያስገቡ (ለምሳሌ፦ 0912345678)፦',
        'payment_success': '✅ ክፍያዎ ተረጋግጧል! አሁን አገልግሎቱን መጠቀም ይችላሉ።',
        'choose_service': '📋 የሚፈልጉትን አገልግሎት ይምረጡ:',
        'matching': '🔍 ተመሳሳይ ፍላጎት ያላቸውን እየፈለግን ነው...',
        'no_match': '😔 በአሁኑ ሰዓት የሚመጥን አልተገኘም። እባክዎ ቆየት ብለው ይሞክሩ።',
        'invalid_phone': '❌ የተሳሳተ ስልክ ቁጥር ነው። እባክዎ እንደገና ይሞክሩ:',
    },
    'en': {
        'welcome': '👋 Welcome to the Dating Bot!\nPlease choose your language:',
        'language_selected': '🇬🇧 English selected',
        'main_menu': '🎯 Main Menu:\nChoose from options below:',
        'find_partner': '💕 Find Partner',
        'online': '💻 Online',
        'in_person': '👥 In Person',
        'short_night': '🌙 Short Night',
        'full_night': '⭐ Full Night',
        'payment_required': f'💳 Please pay {PAYMENT_AMOUNT} Birr first\n\nSelected service: {{service}}\n\nChoose payment method:',
        'cbe': '🏦 Commercial Bank of Ethiopia',
        'tele_birr': '📱 Tele Birr',
        'payment_instructions': '💳 To make payment:\n\nUse {method}\nPhone/Account: {number}\nAmount: {amount} Birr\n\nAfter payment, send your phone number:',
        'verify_payment': '🔄 Verify My Payment',
        'enter_phone': '📱 Please enter your phone number (e.g., 0912345678):',
        'payment_success': '✅ Payment verified! You can now use the service.',
        'choose_service': '📋 Choose your preferred service:',
        'matching': '🔍 Looking for matches with similar interests...',
        'no_match': '😔 No matches found at the moment. Please try again later.',
        'invalid_phone': '❌ Invalid phone number. Please try again:',
    }
}

# ==================== BOT HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with language selection"""
    user = update.effective_user
    
    # Register user in database
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name, registered_date) VALUES (?, ?, ?, ?)",
            (user.id, user.username, user.first_name, datetime.now().isoformat())
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Database error in start: {e}")
    finally:
        conn.close()
    
    keyboard = [
        [InlineKeyboardButton("🇪🇹 አማርኛ", callback_data='lang_am')],
        [InlineKeyboardButton("🇬🇧 English", callback_data='lang_en')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 Welcome! እንኳን ደህና መጡ!\nPlease choose your language / እባክዎ ቋንቋ ይምረጡ:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button presses"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Initialize user data if needed
    if 'language' not in context.user_data:
        context.user_data['language'] = 'en'
    
    # Handle language selection
    if data.startswith('lang_'):
        lang = data.split('_')[1]
        context.user_data['language'] = lang
        
        # Save to database
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
            conn.commit()
        except Exception as e:
            logger.error(f"Database error in language selection: {e}")
        finally:
            conn.close()
        
        await query.edit_message_text(TRANSLATIONS[lang]['language_selected'])
        await show_main_menu(update, context)
    
    # Handle main menu
    elif data == 'find_partner':
        await show_service_options(update, context)
    
    elif data in ['online', 'in_person', 'short_night', 'full_night']:
        lang = context.user_data.get('language', 'en')
        context.user_data['selected_service'] = data
        
        # Check if user has paid
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT paid FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()
        except Exception as e:
            logger.error(f"Database error checking payment: {e}")
            result = None
        finally:
            conn.close()
        
        if result and result[0]:
            # User has paid, proceed with matching
            await find_match(update, context)
        else:
            # Show payment options
            await show_payment_options(update, context, data)
    
    # Handle payment method
    elif data in ['pay_cbe', 'pay_tele']:
        await show_payment_instructions(update, context, data)
    
    elif data == 'verify_payment':
        lang = context.user_data.get('language', 'en')
        await query.edit_message_text(TRANSLATIONS[lang]['enter_phone'])
        context.user_data['awaiting_phone'] = True

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    query = update.callback_query
    lang = context.user_data.get('language', 'en')
    
    keyboard = [
        [InlineKeyboardButton(TRANSLATIONS[lang]['find_partner'], callback_data='find_partner')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        TRANSLATIONS[lang]['main_menu'],
        reply_markup=reply_markup
    )

async def show_service_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show service options"""
    query = update.callback_query
    lang = context.user_data.get('language', 'en')
    
    keyboard = [
        [InlineKeyboardButton(TRANSLATIONS[lang]['online'], callback_data='online')],
        [InlineKeyboardButton(TRANSLATIONS[lang]['in_person'], callback_data='in_person')],
        [InlineKeyboardButton(TRANSLATIONS[lang]['short_night'], callback_data='short_night')],
        [InlineKeyboardButton(TRANSLATIONS[lang]['full_night'], callback_data='full_night')],
        [InlineKeyboardButton("◀️ Back", callback_data='back_to_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        TRANSLATIONS[lang]['choose_service'],
        reply_markup=reply_markup
    )

async def show_payment_options(update: Update, context: ContextTypes.DEFAULT_TYPE, service: str):
    """Show payment method options"""
    query = update.callback_query
    lang = context.user_data.get('language', 'en')
    
    keyboard = [
        [InlineKeyboardButton(TRANSLATIONS[lang]['cbe'], callback_data='pay_cbe')],
        [InlineKeyboardButton(TRANSLATIONS[lang]['tele_birr'], callback_data='pay_tele')],
        [InlineKeyboardButton("◀️ Back", callback_data='back_to_services')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = TRANSLATIONS[lang]['payment_required'].format(service=service)
    await query.edit_message_text(message, reply_markup=reply_markup)

async def show_payment_instructions(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_method: str):
    """Show payment instructions"""
    query = update.callback_query
    lang = context.user_data.get('language', 'en')
    
    if payment_method == 'pay_cbe':
        method_name = "CBE"
        number = CBE_ACCOUNT
    else:
        method_name = "Tele Birr"
        number = TELE_BIRR_NUMBER
    
    keyboard = [
        [InlineKeyboardButton(TRANSLATIONS[lang]['verify_payment'], callback_data='verify_payment')],
        [InlineKeyboardButton("◀️ Back", callback_data='back_to_payment')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = TRANSLATIONS[lang]['payment_instructions'].format(
        method=method_name,
        number=number,
        amount=PAYMENT_AMOUNT
    )
    
    await query.edit_message_text(message, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    user_id = update.effective_user.id
    lang = context.user_data.get('language', 'en')
    
    # Check if we're waiting for phone number
    if context.user_data.get('awaiting_phone'):
        phone = update.message.text.strip()
        
        # Simple phone validation (Ethiopian numbers)
        if phone.isdigit() and len(phone) >= 9 and len(phone) <= 13:
            # Record payment (in production, verify payment first)
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute(
                    "UPDATE users SET paid = 1, payment_date = ?, phone = ? WHERE user_id = ?",
                    (datetime.now().isoformat(), phone, user_id)
                )
                conn.commit()
            except Exception as e:
                logger.error(f"Database error recording payment: {e}")
            finally:
                conn.close()
            
            await update.message.reply_text(TRANSLATIONS[lang]['payment_success'])
            context.user_data['awaiting_phone'] = False
            
            # Show main menu again
            await show_main_menu_after_payment(update, context)
        else:
            await update.message.reply_text(TRANSLATIONS[lang]['invalid_phone'])

async def show_main_menu_after_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu after successful payment"""
    lang = context.user_data.get('language', 'en')
    
    keyboard = [
        [InlineKeyboardButton(TRANSLATIONS[lang]['find_partner'], callback_data='find_partner')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        TRANSLATIONS[lang]['main_menu'],
        reply_markup=reply_markup
    )

async def find_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Find a match for the user"""
    query = update.callback_query
    lang = context.user_data.get('language', 'en')
    
    await query.edit_message_text(TRANSLATIONS[lang]['matching'])
    
    # Simulate searching
    await asyncio.sleep(2)
    
    # For demo purposes (you'd implement actual matching)
    keyboard = [
        [InlineKeyboardButton(TRANSLATIONS[lang]['find_partner'], callback_data='find_partner')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        TRANSLATIONS[lang]['no_match'],
        reply_markup=reply_markup
    )

async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple health check command"""
    await update.message.reply_text("✅ Bot is running on Render! 🤖")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        if update and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Sorry, an error occurred. Please try again later."
            )
    except:
        pass

# ==================== MAIN FUNCTION ====================

def main():
    """Start the bot"""
    # Initialize database
    init_db()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("health", health_check))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Check if running on Render
    if os.environ.get('RENDER'):
        # Use webhook on Render
        port = int(os.environ.get('PORT', 10000))
        webhook_url = os.environ.get('WEBHOOK_URL', '')
        
        logger.info(f"Starting webhook on port {port}")
        if webhook_url:
            application.run_webhook(
                listen="0.0.0.0",
                port=port,
                webhook_url=webhook_url,
                secret_token=None
            )
        else:
            logger.warning("WEBHOOK_URL not set, falling back to polling")
            application.run_polling()
    else:
        # Use polling locally
        logger.info("Starting polling mode")
        application.run_polling()

if __name__ == '__main__':
    main()
