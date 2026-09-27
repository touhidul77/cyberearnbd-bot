from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

ADMIN_TELEGRAM_ID = 6682080873
DATABASE = 'database.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            telegram_id TEXT PRIMARY KEY,
            name TEXT,
            balance REAL DEFAULT 0,
            coins INTEGER DEFAULT 0,
            ads_watched INTEGER DEFAULT 0,
            referrals_count INTEGER DEFAULT 0,
            referred_by TEXT,
            is_banned INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT,
            amount REAL,
            method TEXT,
            number TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/api/user', methods=['POST'])
def get_or_create_user():
    data = request.json
    telegram_id = str(data.get('telegram_id'))
    name = data.get('name', 'User')
    referred_by = data.get('referred_by')

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cursor.fetchone()

    if not user:
        # Check referral
        if referred_by and referred_by != telegram_id:
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (referred_by,))
            ref_user = cursor.fetchone()
            if ref_user:
                cursor.execute('UPDATE users SET coins = coins + 200, referrals_count = referrals_count + 1 WHERE telegram_id = ?', (referred_by,))
        
        cursor.execute('INSERT INTO users (telegram_id, name, referred_by) VALUES (?, ?, ?)', (telegram_id, name, referred_by))
        conn.commit()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()

    conn.close()
    
    return jsonify({
        'telegram_id': user[0],
        'name': user[1],
        'balance': user[2],
        'coins': user[3],
        'ads_watched': user[4],
        'referrals_count': user[5],
        'is_admin': (user[0] == str(ADMIN_TELEGRAM_ID)),
        'is_banned': user[7]
    })

@app.route('/api/watch-ad', methods=['POST'])
def watch_ad():
    data = request.json
    telegram_id = str(data.get('telegram_id'))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # 1 coin = 1 paisa -> 20 coins = 0.20 BDT (or adjust as needed, here 20 coins added)
    cursor.execute('UPDATE users SET coins = coins + 20, ads_watched = ads_watched + 1, balance = balance + 0.20 WHERE telegram_id = ?', (telegram_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': '20 কয়েন সফলভাবে যোগ হয়েছে!'})

@app.route('/api/withdraw', methods=['POST'])
def withdraw():
    data = request.json
    telegram_id = str(data.get('telegram_id'))
    amount = float(data.get('amount'))
    method = data.get('method')
    number = data.get('number')

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT coins, ads_watched, referrals_count FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cursor.fetchone()

    if not user:
        return jsonify({'success': False, 'message': 'ইউজার পাওয়া যায়নি!'}), 400

    coins, ads_watched, referrals_count = user
    taka = coins / 100 # 100 coins = 1 BDT or adjust based on your logic (1 coin = 1 paisa means 100 coins = 1 BDT)

    if amount < 100:
        return jsonify({'success': False, 'message': 'মিনিমাম ১০০ টাকা হতে হবে!'}), 400

    # First time condition: 15 referrals and 100 ads watched
    # Checking historical withdrawals count
    cursor.execute('SELECT COUNT(*) FROM withdrawals WHERE telegram_id = ?', (telegram_id,))
    total_withdrawals = cursor.fetchone()[0]

    if total_withdrawals == 0:
        if referrals_count < 15 or ads_watched < 100:
            return jsonify({'success': False, 'message': 'প্রথম উড্রো করার জন্য অন্তত ১৫টি রেফার এবং ১০০টি এড দেখা বাধ্যতামূলক!'}), 400

    if taka < amount:
        return jsonify({'success': False, 'message': 'পর্যাপ্ত ব্যালেন্স নেই!'}), 400

    new_coins = coins - (amount * 100)
    cursor.execute('UPDATE users SET coins = ? WHERE telegram_id = ?', (new_coins, telegram_id))
    cursor.execute('INSERT INTO withdrawals (telegram_id, amount, method, number) VALUES (?, ?, ?, ?)', (telegram_id, amount, method, number))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'উড্রো রিকোয়েস্ট সফলভাবে সাবমিট হয়েছে!'})

@app.route('/api/admin/data', methods=['GET'])
def admin_data():
    admin_id = request.args.get('telegram_id')
    if str(admin_id) != str(ADMIN_TELEGRAM_ID):
        return jsonify({'error': 'Unauthorized'}), 403

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT telegram_id, name, balance, coins, ads_watched, referrals_count, is_banned FROM users')
    users = cursor.fetchall()

    cursor.execute('SELECT id, telegram_id, amount, method, number, status FROM withdrawals')
    withdrawals = cursor.fetchall()
    conn.close()

    return jsonify({'users': users, 'withdrawals': withdrawals})

@app.route('/api/admin/action', methods=['POST'])
def admin_action():
    data = request.json
    admin_id = str(data.get('telegram_id'))
    if admin_id != str(ADMIN_TELEGRAM_ID):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    action_type = data.get('type') # 'complete_withdraw', 'ban_user'
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    if action_type == 'complete_withdraw':
        w_id = data.get('id')
        cursor.execute("UPDATE withdrawals SET status = 'Completed' WHERE id = ?", (w_id,))
    elif action_type == 'ban_user':
        target_id = data.get('target_id')
        cursor.execute("UPDATE users SET is_banned = 1 WHERE telegram_id = ?", (target_id,))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)