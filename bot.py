import logging
import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Configuration Variables
BOT_TOKEN = "8845992911:AAFQ5-2n9E8-nzuJuffFAV9noljFz12A0cM"
MINI_APP_URL = "https://cyberearnbd.netlify.app"
REFERRAL_BONUS = 200  # 200 Coins

# Simple In-Memory Database
user_balances = {}
user_referrals = {}

# ------------------- Flask Web Server for Render -------------------
flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return "Cyber Earn BD Bot is Running Live 24/7!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

# ------------------- Telegram Bot Handlers -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Initialize user profile
    if user_id not in user_balances:
        user_balances[user_id] = 0
        user_referrals[user_id] = 0

    # Referral system check
    if context.args:
        try:
            referrer_id = int(context.args[0])
            if referrer_id != user_id and referrer_id in user_balances:
                # Award referral bonus
                user_balances[referrer_id] += REFERRAL_BONUS
                user_referrals[referrer_id] += 1
                
                # Notify referrer
                await context.bot.send_message(
                    chat_id=referrer_id,
                    text=f"🎉 নতুন রেফারেল সংযোগ হয়েছে!\nআপনি পেয়েছেন {REFERRAL_BONUS} কয়েন।"
                )
        except ValueError:
            pass

    # Referral link creation
    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"

    # Buttons layout (web_app ব্যবহার করা হয়েছে)
    keyboard = [
        [InlineKeyboardButton("📱 Open App & Earn", web_app=WebAppInfo(url=f"{MINI_APP_URL}?user_id={user_id}"))],
        [InlineKeyboardButton("🔗 Share Referral Link", url=f"https://t.me/share/url?url={ref_link}&text=Join%20Cyber%20Earn%20BD%20and%20earn%20money!")],
        [InlineKeyboardButton("💰 Check Balance", callback_data="check_balance")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_msg = (
        f"👋 **হ্যালো {user.first_name}!**\n\n"
        f"**Cyber Earn BD**-তে আপনাকে স্বাগতম!\n\n"
        f"🎯 **কীভাবে ইনকাম করবেন?**\n"
        f"• Ads দেখে ইনকাম করুন (প্রতি এড 10 কয়েন)\n"
        f"• প্রতি রেফারে পান **{REFERRAL_BONUS} কয়েন**\n\n"
        f"👇 নিচের বাটনে ক্লিক করে কাজ শুরু করুন:"
    )

    await update.message.reply_text(welcome_msg, reply_markup=reply_markup, parse_mode="Markdown")

# ------------------- Main Execution -------------------
def main():
    # 1. Background-এ Flask Web Server রান করা
    threading.Thread(target=run_flask, daemon=True).start()

    # 2. Telegram Bot Application বিল্ড ও রান করা
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers নিবন্ধন
    application.add_handler(CommandHandler("start", start))

    # Bot Polling শুরু
    logging.info("Starting bot polling...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
