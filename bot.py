import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

TOKEN = "8755787279:AAFg-QCxyUZ8fCthQOE83Fn9sCmh0qagvAc"
WEB_APP_URL = "https://cyberearnbd.netlify.app/" # আপনার নেটলিফাই লিংক এখানে দিন

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [[InlineKeyboardButton("🚀 Cyber Point BD ওপেন করুন", web_app=WebAppInfo(url=WEB_APP_URL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"আসসালামু আলাইকুম, {user.first_name}!\n\n"
        "Cyber Point BD টেলিগ্রাম মিনি অ্যাপে আপনাকে স্বাগতম। নিচে ক্লিক করে অ্যাপটি ওপেন করুন এবং আয় শুরু করুন!",
        reply_markup=reply_markup
    )

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()