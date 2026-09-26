"""
Cyber Earn BD - Telegram Bot & WebApp Backend API (FastAPI)
Updated with automatic Telegram Webhook registration on startup.
"""

import os
import json
import sqlite3
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN", "8845992911:AAFQ5-2n9E8-nzuJuffFAV9noljFz12A0cM")
# আপনার রেন্ডার সার্ভারের সঠিক ইউআরএল এখানে বসানো হয়েছে
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://cyberearnbd-bot.onrender.com")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://cyberearnbd.netlify.app/")
CHANNEL_URL = "https://t.me/CyberEarnBD_Official"
GROUP_URL = "https://t.me/CyberEarnBD_Community"

app = FastAPI(title="Cyber Earn BD Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "cyber_earn.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                coins INTEGER DEFAULT 0,
                ads_watched INTEGER DEFAULT 0,
                referrals_count INTEGER DEFAULT 0,
                referred_by TEXT,
                has_withdrawn_before INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawals (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                method TEXT,
                account_no TEXT,
                amount_bdt REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print("Database Initialization Error:", str(e))

init_db()

# Startup event to register Telegram Webhook automatically
@app.on_event("startup")
def set_telegram_webhook():
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook/{BOT_TOKEN}"
        tg_api = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}"
        try:
            res = requests.get(tg_api)
            print("Webhook Setup Response:", res.json())
        except Exception as e:
            print("Webhook Setup Failed:", str(e))

class UserDataSync(BaseModel):
    user_id: str
    first_name: str
    username: Optional[str] = None
    referred_by: Optional[str] = None
    coins: Optional[int] = None
    ads_watched: Optional[int] = None

class WithdrawRequest(BaseModel):
    user_id: str
    method: str
    account_no: str
    amount_bdt: float

@app.get("/")
def read_root():
    return {"status": "online", "app": "Cyber Earn BD Backend Service", "version": "2.1"}

@app.post("/api/user/sync")
def sync_user(data: UserDataSync):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (data.user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, first_name, username, referred_by) VALUES (?, ?, ?, ?)",
            (data.user_id, data.first_name, data.username, data.referred_by)
        )
        
        if data.referred_by and data.referred_by != data.user_id:
            cursor.execute(
                "UPDATE users SET coins = coins + 200, referrals_count = referrals_count + 1 WHERE user_id = ?",
                (data.referred_by,)
            )
        conn.commit()
    else:
        if data.coins is not None and data.ads_watched is not None:
            cursor.execute(
                "UPDATE users SET coins = ?, ads_watched = ? WHERE user_id = ?",
                (data.coins, data.ads_watched, data.user_id)
            )
            conn.commit()

    cursor.execute("SELECT user_id, coins, ads_watched, referrals_count, has_withdrawn_before FROM users WHERE user_id = ?", (data.user_id,))
    res = cursor.fetchone()
    conn.close()

    return {
        "user_id": res[0],
        "coins": res[1],
        "ads_watched": res[2],
        "referrals": res[3],
        "has_withdrawn_before": bool(res[4])
    }

@app.post(f"/webhook/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        
        if "message" in data:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"].get("text", "")
            
            if text.startswith("/start"):
                welcome_text = (
                    f"👋 **স্বাগতম Cyber Earn BD-তে!**\n\n"
                    f"এখানে আপনি অ্যাড দেখে এবং বন্ধুদের রেফার করে খুব সহজেই প্রতিদিন ভালো টাকা ইনকাম করতে পারবেন।\n\n"
                    f"📢 **চ্যানেল:** [Cyber Earn BD Official]({CHANNEL_URL})\n"
                    f"💬 **গ্রুপ:** [Cyber Earn BD Community]({GROUP_URL})\n\n"
                    f"নিচের **'🚀 ওপেন মিনি অ্যাপ'** বাটনে ক্লিক করে কাজ শুরু করুন।"
                )

                keyboard = {
                    "inline_keyboard": [
                        [{"text": "🚀 ওপেন মিনি অ্যাপ", "web_app": {"url": WEBAPP_URL}}],
                        [{"text": "📢 চ্যানেল", "url": CHANNEL_URL}, {"text": "💬 গ্রুপ", "url": GROUP_URL}]
                    ]
                }

                telegram_api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": welcome_text,
                    "parse_mode": "Markdown",
                    "reply_markup": json.dumps(keyboard)
                }
                requests.post(telegram_api_url, json=payload)
    except Exception as e:
        print("Webhook Error:", str(e))

    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
