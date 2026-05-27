"""
Telegram Shop Bot - pyTelegramBotAPI
Deploy: Railway / VPS
"""
import os
import sqlite3
import threading
import time
from datetime import datetime

import telebot
from telebot import types

# ============== CONFIG ==============
BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip().isdigit()]

GROUP_LINK = "https://t.me/xombaoref"
ADMIN_LINK = "https://t.me/luxvipb"

VIETQR_IMAGE = "https://api.vietqr.io/image/970449-0344127655-HxJXGbk.jpg"
BANK_NAME = "MB Bank"
BANK_ACCOUNT = "0344127655"
BANK_HOLDER = "CHU TAI KHOAN"

QR_AUTO_DELETE_SECONDS = 15 * 60  # 15 phút

DB_PATH = os.getenv("DB_PATH", "shop.db")

# ============== TOOLS LIST ==============
TOOLS = {
    "tool_1": {"name": "Tool gộp 180 kèm tim", "price": 180000},
    "tool_2": {"name": "Tool tương tác", "price": 20000},
    "tool_3": {"name": "Tool chạy ref", "price": 20000},
    "tool_4": {"name": "Tool spam", "price": 50000},
    "tool_5": {"name": "Tool buff mem", "price": 20000},
    "tool_6": {"name": "Tool lấy acc đọc tn session", "price": 50000},
}

# ============== BOT ==============
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ============== DB ==============
_db_lock = threading.Lock()

def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        balance INTEGER DEFAULT 0,
        banned INTEGER DEFAULT 0,
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS deposits(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        method TEXT,
        status TEXT,
        created_at TEXT,
        approved_at TEXT
    );
    CREATE TABLE IF NOT EXISTS purchases(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        tool_key TEXT,
        tool_name TEXT,
        price INTEGER,
        created_at TEXT
    );
    """)
    conn.commit()
    conn.close()

def ensure_user(u):
    with _db_lock:
        conn = db()
        c = conn.cursor()
        c.execute("SELECT user_id FROM users WHERE user_id=?", (u.id,))
        if not c.fetchone():
            c.execute(
                "INSERT INTO users(user_id, username, full_name, balance, banned, created_at) VALUES (?,?,?,0,0,?)",
                (u.id, u.username or "", (u.first_name or "") + " " + (u.last_name or ""), now()),
            )
        else:
            c.execute("UPDATE users SET username=?, full_name=? WHERE user_id=?",
                      (u.username or "", (u.first_name or "") + " " + (u.last_name or ""), u.id))
        conn.commit()
        conn.close()

def get_user(uid):
    conn = db()
    r = conn.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    conn.close()
    return r

def update_balance(uid, delta):
    with _db_lock:
        conn = db()
        conn.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (delta, uid))
        conn.commit()
        conn.close()

def set_banned(uid, value):
    with _db_lock:
        conn = db()
        conn.execute("UPDATE users SET banned=? WHERE user_id=?", (1 if value else 0, uid))
        conn.commit()
        conn.close()

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def is_admin(uid):
    return uid in ADMIN_IDS

def fmt_money(n):
    return f"{int(n):,}đ".replace(",", ".")

# ============== KEYBOARDS ==============
def main_menu_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🛒 Thuê Tool", callback_data="menu_tools"),
        types.InlineKeyboardButton("💳 Nạp tiền", callback_data="menu_deposit"),
        types.InlineKeyboardButton("👤 Cá nhân", callback_data="menu_profile"),
        types.InlineKeyboardButton("🎧 Admin", url=ADMIN_LINK),
        types.InlineKeyboardButton("🤖 BOT CHẠY TOOL", url=GROUP_LINK),
    )
    return kb

def back_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Quay lại", callback_data="back_main"))
    return kb

def tools_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    for k, v in TOOLS.items():
        kb.add(types.InlineKeyboardButton(f"{v['name']} - {fmt_money(v['price'])}", callback_data=f"buy_{k}"))
    kb.add(types.InlineKeyboardButton("⬅️ Quay lại", callback_data="back_main"))
    return kb

def confirm_buy_kb(tool_key):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ Xác nhận", callback_data=f"confirm_{tool_key}"),
        types.InlineKeyboardButton("❌ Hủy", callback_data="menu_tools"),
    )
    return kb

def profile_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📜 Lịch sử nạp", callback_data="hist_deposit"),
        types.InlineKeyboardButton("🧾 Lịch sử tool", callback_data="hist_tool"),
        types.InlineKeyboardButton("⬅️ Quay lại", callback_data="back_main"),
    )
    return kb

# ============== HANDLERS ==============
@bot.message_handler(commands=["start"])
def cmd_start(m):
    ensure_user(m.from_user)
    u = get_user(m.from_user.id)
    if u["banned"]:
        bot.reply_to(m, "🚫 Tài khoản của bạn đã bị khóa.")
        return
    text = (
        f"👋 Xin chào <b>{m.from_user.first_name}</b>!\n\n"
        f"🤖 <b>SHOP TOOL TELEGRAM</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{m.from_user.id}</code>\n"
        f"💰 Số dư: <b>{fmt_money(u['balance'])}</b>\n\n"
        f"👥 Nhóm: {GROUP_LINK}\n"
        f"🎧 Admin: {ADMIN_LINK}\n\n"
        f"Chọn chức năng bên dưới 👇"
    )
    bot.send_message(m.chat.id, text, reply_markup=main_menu_kb(), disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda c: c.data == "back_main")
def cb_back(c):
    ensure_user(c.from_user)
    u = get_user(c.from_user.id)
    text = (
        f"🤖 <b>SHOP TOOL TELEGRAM</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{c.from_user.id}</code>\n"
        f"💰 Số dư: <b>{fmt_money(u['balance'])}</b>\n\n"
        f"Chọn chức năng bên dưới 👇"
    )
    try:
        bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=main_menu_kb())
    except Exception:
        bot.send_message(c.message.chat.id, text, reply_markup=main_menu_kb())
    bot.answer_callback_query(c.id)

# -------- Tools menu --------
@bot.callback_query_handler(func=lambda c: c.data == "menu_tools")
def cb_tools(c):
    text = "🛒 <b>DANH SÁCH TOOL</b>\n━━━━━━━━━━━━━━━━━━\nChọn tool bạn muốn thuê:"
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=tools_kb())
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def cb_buy(c):
    key = c.data[4:]
    tool = TOOLS.get(key)
    if not tool:
        bot.answer_callback_query(c.id, "Không tìm thấy tool"); return
    u = get_user(c.from_user.id)
    text = (
        f"🛒 <b>XÁC NHẬN MUA TOOL</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📦 Tên: <b>{tool['name']}</b>\n"
        f"💵 Giá: <b>{fmt_money(tool['price'])}</b>\n"
        f"💰 Số dư: <b>{fmt_money(u['balance'])}</b>\n\n"
        f"Bạn có chắc chắn muốn mua?"
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=confirm_buy_kb(key))
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_"))
def cb_confirm(c):
    key = c.data[8:]
    tool = TOOLS.get(key)
    if not tool:
        bot.answer_callback_query(c.id, "Không tìm thấy tool"); return
    u = get_user(c.from_user.id)
    if u["banned"]:
        bot.answer_callback_query(c.id, "Tài khoản bị khóa", show_alert=True); return
    if u["balance"] < tool["price"]:
        bot.answer_callback_query(c.id, "❌ Số dư không đủ!", show_alert=True)
        bot.edit_message_text(
            f"❌ <b>Số dư không đủ!</b>\n\nCần: {fmt_money(tool['price'])}\nHiện có: {fmt_money(u['balance'])}\n\nVui lòng nạp thêm tiền.",
            c.message.chat.id, c.message.message_id, reply_markup=back_kb()
        )
        return
    update_balance(c.from_user.id, -tool["price"])
    with _db_lock:
        conn = db()
        conn.execute(
            "INSERT INTO purchases(user_id, tool_key, tool_name, price, created_at) VALUES (?,?,?,?,?)",
            (c.from_user.id, key, tool["name"], tool["price"], now()),
        )
        conn.commit(); conn.close()
    new_u = get_user(c.from_user.id)
    text = (
        f"✅ <b>MUA TOOL THÀNH CÔNG!</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📦 Tool: <b>{tool['name']}</b>\n"
        f"💵 Giá: <b>{fmt_money(tool['price'])}</b>\n"
        f"💰 Số dư còn: <b>{fmt_money(new_u['balance'])}</b>\n\n"
        f"📞 Liên hệ admin để nhận tool: {ADMIN_LINK}"
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=back_kb(), disable_web_page_preview=True)
    # báo admin
    for aid in ADMIN_IDS:
        try:
            bot.send_message(
                aid,
                f"🛒 <b>USER MUA TOOL</b>\n"
                f"👤 {c.from_user.first_name} (@{c.from_user.username or '-'})\n"
                f"🆔 <code>{c.from_user.id}</code>\n"
                f"📦 {tool['name']}\n"
                f"💵 {fmt_money(tool['price'])}"
            )
        except Exception:
            pass
    bot.answer_callback_query(c.id, "✅ Thành công!")

# -------- Profile --------
@bot.callback_query_handler(func=lambda c: c.data == "menu_profile")
def cb_profile(c):
    u = get_user(c.from_user.id)
    text = (
        f"👤 <b>THÔNG TIN CÁ NHÂN</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{c.from_user.id}</code>\n"
        f"👤 Tên: <b>{c.from_user.first_name}</b>\n"
        f"💰 Số dư: <b>{fmt_money(u['balance'])}</b>\n"
        f"📅 Tham gia: {u['created_at']}\n"
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=profile_kb())
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "hist_deposit")
def cb_hist_dep(c):
    conn = db()
    rows = conn.execute(
        "SELECT * FROM deposits WHERE user_id=? AND status='approved' ORDER BY id DESC LIMIT 20",
        (c.from_user.id,)
    ).fetchall()
    conn.close()
    if not rows:
        text = "📜 <b>LỊCH SỬ NẠP</b>\n\nChưa có giao dịch nào."
    else:
        lines = ["📜 <b>LỊCH SỬ NẠP</b>", "━━━━━━━━━━━━━━━━━━", "<code>Thời gian | Số tiền | Kênh</code>"]
        for r in rows:
            lines.append(f"<code>{r['approved_at'] or r['created_at']} | {fmt_money(r['amount'])} | {r['method']}</code>")
        text = "\n".join(lines)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Quay lại", callback_data="menu_profile"))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=kb)
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "hist_tool")
def cb_hist_tool(c):
    conn = db()
    rows = conn.execute(
        "SELECT * FROM purchases WHERE user_id=? ORDER BY id DESC LIMIT 20",
        (c.from_user.id,)
    ).fetchall()
    conn.close()
    if not rows:
        text = "🧾 <b>LỊCH SỬ TOOL</b>\n\nChưa mua tool nào."
    else:
        lines = ["🧾 <b>LỊCH SỬ TOOL</b>", "━━━━━━━━━━━━━━━━━━"]
        for r in rows:
            lines.append(f"• {r['created_at']} | {r['tool_name']} | {fmt_money(r['price'])}")
        text = "\n".join(lines)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⬅️ Quay lại", callback_data="menu_profile"))
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=kb)
    bot.answer_callback_query(c.id)

# -------- Deposit menu --------
@bot.callback_query_handler(func=lambda c: c.data == "menu_deposit")
def cb_dep(c):
    text = (
        f"💳 <b>NẠP TIỀN</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Để nạp tiền, gõ lệnh:\n"
        f"<code>/naptien &lt;số tiền&gt;</code>\n\n"
        f"Ví dụ: <code>/naptien 10000</code>\n\n"
        f"Hệ thống sẽ tạo QR VietQR tự động."
    )
    bot.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=back_kb())
    bot.answer_callback_query(c.id)

# -------- /naptien --------
@bot.message_handler(commands=["naptien"])
def cmd_naptien(m):
    ensure_user(m.from_user)
    u = get_user(m.from_user.id)
    if u["banned"]:
        bot.reply_to(m, "🚫 Tài khoản đã bị khóa."); return
    parts = m.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        bot.reply_to(m, "❌ Sai cú pháp.\nDùng: <code>/naptien &lt;số tiền&gt;</code>\nVí dụ: <code>/naptien 10000</code>")
        return
    amount = int(parts[1])
    if amount < 1000:
        bot.reply_to(m, "❌ Số tiền tối thiểu là 1.000đ"); return

    with _db_lock:
        conn = db()
        cur = conn.execute(
            "INSERT INTO deposits(user_id, amount, method, status, created_at) VALUES (?,?,?,?,?)",
            (m.from_user.id, amount, "VietQR", "pending", now()),
        )
        dep_id = cur.lastrowid
        conn.commit(); conn.close()

    content = f"NAP{m.from_user.id}"
    caption = (
        f"💳 <b>YÊU CẦU NẠP TIỀN</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏦 Ngân hàng: <b>{BANK_NAME}</b>\n"
        f"💳 Số TK: <code>{BANK_ACCOUNT}</code>\n"
        f"👤 Chủ TK: <b>{BANK_HOLDER}</b>\n"
        f"💵 Số tiền: <b>{fmt_money(amount)}</b>\n"
        f"📝 Nội dung CK: <code>{content}</code>\n\n"
        f"⏰ QR sẽ tự xóa sau <b>15 phút</b>.\n"
        f"⚠️ Vui lòng ghi đúng nội dung CK!"
    )
    sent = bot.send_photo(m.chat.id, VIETQR_IMAGE, caption=caption)

    # auto xóa sau 15p
    def _auto_delete(chat_id, msg_id):
        time.sleep(QR_AUTO_DELETE_SECONDS)
        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass
    threading.Thread(target=_auto_delete, args=(sent.chat.id, sent.message_id), daemon=True).start()

    # báo admin
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ DUYỆT", callback_data=f"approve_{dep_id}"),
        types.InlineKeyboardButton("❌ TỪ CHỐI", callback_data=f"reject_{dep_id}"),
    )
    admin_text = (
        f"🔔 <b>YÊU CẦU NẠP TIỀN</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🆔 Mã GD: <code>#{dep_id}</code>\n"
        f"👤 User: {m.from_user.first_name} (@{m.from_user.username or '-'})\n"
        f"🆔 User ID: <code>{m.from_user.id}</code>\n"
        f"💵 Số tiền: <b>{fmt_money(amount)}</b>\n"
        f"📝 Nội dung: <code>{content}</code>\n"
        f"⏰ {now()}"
    )
    for aid in ADMIN_IDS:
        try:
            bot.send_message(aid, admin_text, reply_markup=kb)
        except Exception:
            pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("approve_"))
def cb_approve(c):
    if not is_admin(c.from_user.id):
        bot.answer_callback_query(c.id, "Bạn không có quyền!", show_alert=True); return
    dep_id = int(c.data.split("_")[1])
    conn = db()
    r = conn.execute("SELECT * FROM deposits WHERE id=?", (dep_id,)).fetchone()
    conn.close()
    if not r:
        bot.answer_callback_query(c.id, "Không tìm thấy"); return
    if r["status"] != "pending":
        bot.answer_callback_query(c.id, f"GD đã {r['status']}", show_alert=True); return
    update_balance(r["user_id"], r["amount"])
    with _db_lock:
        conn = db()
        conn.execute("UPDATE deposits SET status='approved', approved_at=? WHERE id=?", (now(), dep_id))
        conn.commit(); conn.close()
    try:
        bot.edit_message_text(
            c.message.text + f"\n\n✅ <b>ĐÃ DUYỆT</b> bởi {c.from_user.first_name}",
            c.message.chat.id, c.message.message_id
        )
    except Exception:
        pass
    try:
        u = get_user(r["user_id"])
        bot.send_message(
            r["user_id"],
            f"✅ <b>NẠP TIỀN THÀNH CÔNG!</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💵 Số tiền: <b>{fmt_money(r['amount'])}</b>\n"
            f"💰 Số dư hiện tại: <b>{fmt_money(u['balance'])}</b>\n"
            f"⏰ {now()}"
        )
    except Exception:
        pass
    bot.answer_callback_query(c.id, "✅ Đã duyệt")

@bot.callback_query_handler(func=lambda c: c.data.startswith("reject_"))
def cb_reject(c):
    if not is_admin(c.from_user.id):
        bot.answer_callback_query(c.id, "Bạn không có quyền!", show_alert=True); return
    dep_id = int(c.data.split("_")[1])
    with _db_lock:
        conn = db()
        r = conn.execute("SELECT * FROM deposits WHERE id=?", (dep_id,)).fetchone()
        if not r or r["status"] != "pending":
            conn.close()
            bot.answer_callback_query(c.id, "Không hợp lệ"); return
        conn.execute("UPDATE deposits SET status='rejected', approved_at=? WHERE id=?", (now(), dep_id))
        conn.commit(); conn.close()
    try:
        bot.edit_message_text(c.message.text + f"\n\n❌ <b>TỪ CHỐI</b>", c.message.chat.id, c.message.message_id)
    except Exception:
        pass
    try:
        bot.send_message(r["user_id"], f"❌ Yêu cầu nạp <b>{fmt_money(r['amount'])}</b> đã bị từ chối.")
    except Exception:
        pass
    bot.answer_callback_query(c.id, "Đã từ chối")

# ============== ADMIN PANEL ==============
def admin_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("👥 Tổng user", callback_data="adm_total"),
        types.InlineKeyboardButton("🔍 Xem user", callback_data="adm_view"),
        types.InlineKeyboardButton("➕ Cộng tiền", callback_data="adm_add"),
        types.InlineKeyboardButton("➖ Trừ tiền", callback_data="adm_sub"),
        types.InlineKeyboardButton("🚫 Khóa user", callback_data="adm_ban"),
        types.InlineKeyboardButton("✅ Mở khóa", callback_data="adm_unban"),
        types.InlineKeyboardButton("📜 Lịch sử user", callback_data="adm_hist"),
    )
    return kb

@bot.message_handler(commands=["admin"])
def cmd_admin(m):
    if not is_admin(m.from_user.id):
        bot.reply_to(m, "🚫 Bạn không phải admin."); return
    bot.send_message(m.chat.id, "🎧 <b>ADMIN PANEL</b>\n━━━━━━━━━━━━━━━━━━\nChọn chức năng:", reply_markup=admin_kb())

@bot.callback_query_handler(func=lambda c: c.data == "adm_total")
def adm_total(c):
    if not is_admin(c.from_user.id): return
    conn = db()
    total = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
    total_bal = conn.execute("SELECT COALESCE(SUM(balance),0) AS s FROM users").fetchone()["s"]
    total_dep = conn.execute("SELECT COALESCE(SUM(amount),0) AS s FROM deposits WHERE status='approved'").fetchone()["s"]
    total_buy = conn.execute("SELECT COUNT(*) AS n FROM purchases").fetchone()["n"]
    conn.close()
    bot.answer_callback_query(c.id)
    bot.send_message(
        c.message.chat.id,
        f"📊 <b>THỐNG KÊ</b>\n━━━━━━━━━━━━━━━━━━\n"
        f"👥 Tổng user: <b>{total}</b>\n"
        f"💰 Tổng số dư: <b>{fmt_money(total_bal)}</b>\n"
        f"💵 Tổng nạp: <b>{fmt_money(total_dep)}</b>\n"
        f"🛒 Tổng lượt mua: <b>{total_buy}</b>"
    )

_adm_state = {}  # admin_id -> action

def _ask(c, action, prompt):
    if not is_admin(c.from_user.id): return
    _adm_state[c.from_user.id] = action
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, prompt)

@bot.callback_query_handler(func=lambda c: c.data == "adm_view")
def _(c): _ask(c, "view", "🔍 Nhập <b>User ID</b> cần xem:")

@bot.callback_query_handler(func=lambda c: c.data == "adm_add")
def _(c): _ask(c, "add", "➕ Nhập: <code>user_id số_tiền</code>\nVD: <code>123456 50000</code>")

@bot.callback_query_handler(func=lambda c: c.data == "adm_sub")
def _(c): _ask(c, "sub", "➖ Nhập: <code>user_id số_tiền</code>")

@bot.callback_query_handler(func=lambda c: c.data == "adm_ban")
def _(c): _ask(c, "ban", "🚫 Nhập <b>User ID</b> cần khóa:")

@bot.callback_query_handler(func=lambda c: c.data == "adm_unban")
def _(c): _ask(c, "unban", "✅ Nhập <b>User ID</b> cần mở khóa:")

@bot.callback_query_handler(func=lambda c: c.data == "adm_hist")
def _(c): _ask(c, "hist", "📜 Nhập <b>User ID</b> để xem lịch sử:")

def user_quick_kb(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ Cộng tiền", callback_data=f"q_add_{uid}"),
        types.InlineKeyboardButton("➖ Trừ tiền", callback_data=f"q_sub_{uid}"),
        types.InlineKeyboardButton("🚫 Khóa", callback_data=f"q_ban_{uid}"),
        types.InlineKeyboardButton("✅ Mở", callback_data=f"q_unban_{uid}"),
        types.InlineKeyboardButton("📜 Lịch sử", callback_data=f"q_hist_{uid}"),
    )
    return kb

def show_user(chat_id, uid):
    u = get_user(uid)
    if not u:
        bot.send_message(chat_id, "❌ Không tìm thấy user."); return
    text = (
        f"👤 <b>THÔNG TIN USER</b>\n━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{u['user_id']}</code>\n"
        f"👤 Tên: {u['full_name']}\n"
        f"📛 Username: @{u['username'] or '-'}\n"
        f"💰 Số dư: <b>{fmt_money(u['balance'])}</b>\n"
        f"📅 Tham gia: {u['created_at']}\n"
        f"🚦 Trạng thái: {'🚫 BỊ KHÓA' if u['banned'] else '✅ Hoạt động'}"
    )
    bot.send_message(chat_id, text, reply_markup=user_quick_kb(uid))

def show_user_hist(chat_id, uid):
    conn = db()
    deps = conn.execute("SELECT * FROM deposits WHERE user_id=? ORDER BY id DESC LIMIT 10", (uid,)).fetchall()
    buys = conn.execute("SELECT * FROM purchases WHERE user_id=? ORDER BY id DESC LIMIT 10", (uid,)).fetchall()
    conn.close()
    lines = [f"📜 <b>LỊCH SỬ USER <code>{uid}</code></b>", "━━━━━━━━━━━━━━━━━━", "<b>💳 Nạp tiền:</b>"]
    if deps:
        for r in deps:
            lines.append(f"• {r['created_at']} | {fmt_money(r['amount'])} | {r['status']}")
    else:
        lines.append("Không có")
    lines.append("\n<b>🛒 Mua tool:</b>")
    if buys:
        for r in buys:
            lines.append(f"• {r['created_at']} | {r['tool_name']} | {fmt_money(r['price'])}")
    else:
        lines.append("Không có")
    bot.send_message(chat_id, "\n".join(lines))

@bot.callback_query_handler(func=lambda c: c.data.startswith("q_"))
def cb_quick(c):
    if not is_admin(c.from_user.id):
        bot.answer_callback_query(c.id, "Không có quyền", show_alert=True); return
    _, action, uid = c.data.split("_", 2)
    uid = int(uid)
    if action == "ban":
        set_banned(uid, True); bot.answer_callback_query(c.id, "🚫 Đã khóa", show_alert=True)
    elif action == "unban":
        set_banned(uid, False); bot.answer_callback_query(c.id, "✅ Đã mở khóa", show_alert=True)
    elif action == "hist":
        bot.answer_callback_query(c.id); show_user_hist(c.message.chat.id, uid)
    elif action == "add":
        _adm_state[c.from_user.id] = f"qadd:{uid}"
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, f"➕ Nhập số tiền cộng cho <code>{uid}</code>:")
    elif action == "sub":
        _adm_state[c.from_user.id] = f"qsub:{uid}"
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, f"➖ Nhập số tiền trừ của <code>{uid}</code>:")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.from_user.id in _adm_state)
def admin_input(m):
    action = _adm_state.pop(m.from_user.id)
    txt = m.text.strip()
    try:
        if action == "view":
            show_user(m.chat.id, int(txt))
        elif action == "ban":
            set_banned(int(txt), True); bot.reply_to(m, "🚫 Đã khóa.")
        elif action == "unban":
            set_banned(int(txt), False); bot.reply_to(m, "✅ Đã mở khóa.")
        elif action == "hist":
            show_user_hist(m.chat.id, int(txt))
        elif action in ("add", "sub"):
            uid, amt = txt.split()
            uid = int(uid); amt = int(amt)
            if not get_user(uid):
                bot.reply_to(m, "❌ User không tồn tại"); return
            delta = amt if action == "add" else -amt
            update_balance(uid, delta)
            bot.reply_to(m, f"✅ Đã {'cộng' if delta>0 else 'trừ'} {fmt_money(abs(delta))} cho <code>{uid}</code>")
            try:
                bot.send_message(uid, f"🔔 Số dư đã {'được cộng' if delta>0 else 'bị trừ'} <b>{fmt_money(abs(delta))}</b> bởi admin.")
            except Exception: pass
        elif action.startswith("qadd:") or action.startswith("qsub:"):
            uid = int(action.split(":")[1])
            amt = int(txt)
            delta = amt if action.startswith("qadd") else -amt
            update_balance(uid, delta)
            bot.reply_to(m, f"✅ Đã {'cộng' if delta>0 else 'trừ'} {fmt_money(abs(delta))} cho <code>{uid}</code>")
            try:
                bot.send_message(uid, f"🔔 Số dư đã {'được cộng' if delta>0 else 'bị trừ'} <b>{fmt_money(abs(delta))}</b> bởi admin.")
            except Exception: pass
    except Exception as e:
        bot.reply_to(m, f"❌ Lỗi: {e}")

# ============== MAIN ==============
if __name__ == "__main__":
    init_db()
    print("🤖 Bot started...")
    bot.infinity_polling(timeout=60, long_polling_timeout=30, skip_pending=True)
