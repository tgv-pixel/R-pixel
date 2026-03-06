import logging
import os
import sqlite3
from datetime import datetime
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables (set these in Render)
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
CBE_ACCOUNT = os.environ.get('CBE_ACCOUNT', '1000612391754')
TELE_BIRR_NUMBER = os.environ.get('TELE_BIRR_NUMBER', '0940980555')
PAYMENT_AMOUNT = int(os.environ.get('PAYMENT_AMOUNT', 500))
ADMIN_IDS = [int(id) for id in os.environ.get('ADMIN_IDS', '').split(',') if id]

# Database setup - Use /tmp for Render (ephemeral storage)
DB_PATH = '/tmp/dating_bot.db' if os.environ.get('RENDER') else 'dating_bot.db'

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, 
                  username TEXT,
                  language TEXT DEFAULT 'en',
                  paid INTEGER DEFAULT 0,
                  payment_date TEXT,
                  phone TEXT,
                  registered_date TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS payments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  amount INTEGER,
                  method TEXT,
                  phone TEXT,
                  status TEXT DEFAULT 'pending',
                  date TEXT)''')
    conn.commit()
    conn.close()
    logger.info("Database initialized")

# Language translations (same as before)
TRANSLATIONS = {
    'am': {
        'welcome': '👋 እንኳን ወደ የፍቅር ጓደኝነት ቦት በደህና መጡ!\nእባክዎ ቋንቋ ይምረጡ:',
        'main_menu': '🎯 ዋና ሜኑ፦\nከዚህ በታች ካሉት አማራጮች ይምረጡ:',
        'find_partner': '💕 ጓደኛ ፈልግ',
        'online': '💻 ኦንላይን',
        'in_person': '👥 ፊት ለፊት',
        'short_night': '🌙 አጭር ሌሊት',
        'full_night': '⭐ ሙሉ ሌሊት',
        'payment_required': f'💳 እባክዎ መጀመሪያ {PAYMENT_AMOUNT} ብር ይክፈሉ\n\nመረጡት አገልግሎት: {{service}}\n\nየክፍያ ዘዴ ይምረጡ:',
        'cbe': '🏦 የኢትዮጵያ ንግድ ባንክ',
        'tele_birr': '📱 ቴሌ ብር',
        'payment_instructions': '💳 ክፍያ ለማድረግ፦\n\n{method} ይጠቀሙ\nስልክ ቁጥር: {number}\nመጠን: {PAYMENT_AMOUNT} ብር\n\nከክፍያ በኋላ የክፍያዎን ማረጋገጫ ይላኩ:',
        'enter_phone': '📱 እባክዎ ስልክ ቁጥርዎን ያስገቡ:',
        'payment_success': '✅ ክፍያዎ ተረጋግጧል! አሁን አገልግሎቱን መጠቀም ይችላሉ።',
        'admin_notify': '🔔 አዲስ ክፍያ ጥያቄ\n\nUser: {user_id}\nPhone: {phone}\nMethod: {method}\nደረሰኝ ያረጋግጡ:',
    },
    'en': {
        'welcome': '👋 Welcome to the Dating Bot!\nPlease choose your language:',
        'main_menu': '🎯 Main Menu:\nChoose from options below:',
        'find_partner': '💕 Find Partner',
        'online': '💻 Online',
        'in_person': '👥 In Person',
        'short_night': '🌙 Short Night',
        'full_night': '⭐ Full Night',
        'payment_required': f'💳 Please pay {PAYMENT_AMOUNT} Birr first\n\nSelected service: {{service}}\n\nChoose payment method:',
        'cbe': '🏦 Commercial Bank of Ethiopia',
        'tele_birr': '📱 Tele Birr',
        'payment_instructions': '💳 To make payment:\n\nUse {method}\nNumber: {number}\nAmount: {PAYMENT_AMOUNT} Birr\n\nAfter payment, send your payment confirmation:',
        'enter_phone': '📱 Please enter your phone number:',
        'payment_success': '✅ Payment verified! You can now use the service.',
        'admin_notify': '🔔 New Payment Request\n\nUser: {user_id}\nPhone: {phone}\nMethod: {method}\nPlease verify receipt:',
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with language selection"""
    user = update.effective_user
    
    # Register user in database
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, registered_date) VALUES (?, ?, ?)",
              (user.id, user.username, datetime.now().isoformat()))
    conn.commit()
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

# Add all your other handler functions here (from previous code)
# ... [Include all the button_handler, show_main_menu, etc. functions]

async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple health check command"""
    await update.message.reply_text("✅ Bot is running on Render!")

def main():
    """Start the bot with webhook for Render"""
    # Initialize database
    init_db()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("health", health_check))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Check if running on Render
    if os.environ.get('RENDER'):
        # Use webhook on Render
        port = int(os.environ.get('PORT', 10000))
        webhook_url = os.environ.get('WEBHOOK_URL', '')
        
        if webhook_url:
            application.run_webhook(
                listen="0.0.0.0",
                port=port,
                webhook_url=webhook_url
            )
            logger.info(f"Bot started with webhook on port {port}")
        else:
            logger.warning("WEBHOOK_URL not set, falling back to polling")
            application.run_polling()
    else:
        # Use polling locally
        logger.info("Bot started with polling (local mode)")
        application.run_polling()

if __name__ == '__main__':
    main()
