import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
MINI_APP_URL = "https://your-app-domain.vercel.app"

REFERRAL_BONUS = 200  # ২০০ Coins = ২ টাকা

# ইউজার ডাটাবেজের ডেমো (বাস্তব প্রোডাকশনে SQLite/Firebase ব্যবহার করতে পারেন)
user_balances = {}
registered_users = set()

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = str(user.id)
    
    # ইউজার প্রথমবার আসলে তাকে ডাটাবেজে রেজিস্টার করা
    if user_id not in registered_users:
        registered_users.add(user_id)
        if user_id not in user_balances:
            user_balances[user_id] = 0

        # রেফারেল চেক
        if context.args:
            referrer_id = context.args[0]
            # নিজের রেফারেল লিংকে নিজে ক্লিক করলে বোনাস পাবে না
            if referrer_id != user_id:
                user_balances[referrer_id] = user_balances.get(referrer_id, 0) + REFERRAL_BONUS
                
                # রেফারকারীকে টেলিগ্রামে বার্তা পাঠানো
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 **অভিনন্দন!**\n\nআপনার রেফারেল লিংকে {user.first_name} জয়েন করেছেন! আপনি **{REFERRAL_BONUS} Coins (২ টাকা)** বোনাস পেয়েছেন।"
                    )
                except Exception:
                    pass

    keyboard = [
        [InlineKeyboardButton("🚀 ইনকাম শুরু করুন (Mini App)", web_app=WebAppInfo(url=MINI_APP_URL))],
        [InlineKeyboardButton("📢 অফিশিয়াল চ্যানেল", url="https://t.me/CyberEarnBD_Official")],
        [InlineKeyboardButton("💬 সাপোর্ট ও কমিউনিটি গ্রুপ", url="https://t.me/CyberEarnBD_Community")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"👋 হে {user.first_name}!\n\n"
        f"আমাদের **Cyber Earn BD** মিনি অ্যাপে স্বাগতম!\n\n"
        f"📌 **কাজের নিয়ম ও বোনাস:**\n"
        f"১. প্রতি রেফারে পাবেন **২০০ Coins (২ টাকা)** একদম ফ্রি!\n"
        f"২. অ্যাড দেখতে হলে অবশ্যই **US** বা **UK** VPN চালু করতে হবে।\n"
        f"৩. প্রতি এডে পাবেন **১০ Coins (১০ পয়সা)**।\n"
        f"৪. মিনিমাম উইথড্র **১,০০০০ Coins = ১০০ টাকা** (বিকাশ/নগদ)।\n\n"
        f"নিচের বাটনে ক্লিক করে কাজ শুরু করুন 👇"
    )

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("CyberEarnBD_bot running...")
    app.run_polling()