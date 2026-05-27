import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import threading
import time

# ================= VARIABLES =================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)

# ================= THÔNG TIN =================

ADMIN = "https://t.me/luxvipb"
NHOM = "https://t.me/xombaoref"

# ================= DATA =================

users = {}
pending_nap = {}

nap_history = {}
tool_history = {}

blocked_users = []

# ================= TOOLS =================

TOOLS = {
    "tool1": ("📦 Tool gộp 180 kèm tim", 180000),
    "tool2": ("📈 Tool tương tác", 20000),
    "tool3": ("🚀 Tool chạy ref", 20000),
    "tool4": ("💣 Tool spam", 50000),
    "tool5": ("👑 Tool buff mem", 20000),
    "tool6": ("🔓 Tool lấy acc, đọc tn .session", 50000)
}

# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):

    user_id = message.from_user.id

    if user_id in blocked_users:

        bot.send_message(
            message.chat.id,
            "🔒 Tài khoản của bạn đã bị khóa."
        )
        return

    if user_id not in users:
        users[user_id] = {
            "balance": 0
        }

    text = f"""
👋 Xin chào!

Chào mừng bạn đến với Shop Tool VIP 🚀

• Nạp tối thiểu: 10.000đ
• Hỗ trợ: @luxvipb
• Nhóm trao đổi: {NHOM}

Vui lòng chọn chức năng bên dưới:
"""

    markup = InlineKeyboardMarkup(row_width=2)

    btn1 = InlineKeyboardButton(
        "🛒 Thuê Tool",
        callback_data="thuetool"
    )

    btn2 = InlineKeyboardButton(
        "💳 Nạp tiền",
        callback_data="naptien"
    )

    btn3 = InlineKeyboardButton(
        "👤 Cá nhân",
        callback_data="canhan"
    )

    btn4 = InlineKeyboardButton(
        "🎧 Admin",
        url=ADMIN
    )

    btn5 = InlineKeyboardButton(
        "🤖 BOT CHẠY TOOL",
        callback_data="bottool"
    )

    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5)

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=markup
    )

# ================= NẠP =================

@bot.callback_query_handler(func=lambda c: c.data == "naptien")
def nap_menu(call):

    bot.send_message(
        call.message.chat.id,
        """
💳 Nạp tiền vào tài khoản 💳

Nạp theo cú pháp:
/naptien <Số Tiền>

Ví dụ:
/naptien 10000

⚠️ Số Tiền Nạp tối thiểu: 1000đ
"""
    )

@bot.message_handler(commands=['naptien'])
def naptien(message):

    user_id = message.from_user.id

    try:
        amount = int(message.text.split()[1])
    except:
        bot.reply_to(message, "❌ Sai cú pháp")
        return

    if amount < 1000:
        bot.reply_to(message, "❌ Nạp tối thiểu 1000đ")
        return

    qr = f"https://api.vietqr.io/image/970449-0344127655-HxJXGbk.jpg?amount={amount}&addInfo=NAP{user_id}&accountName=VU%20BAN%20SUP"

    msg = bot.send_photo(
        message.chat.id,
        qr,
        caption=f"""
💳 QR NẠP TIỀN

💰 Số tiền: {amount:,}đ

📝 Nội dung:
NAP{user_id}

⏳ QR có hiệu lực 15 phút.
"""
    )

    markup = InlineKeyboardMarkup()

    duyet = InlineKeyboardButton(
        "✅ DUYỆT",
        callback_data=f"duyet_{user_id}_{amount}"
    )

    markup.add(duyet)

    admin_msg = bot.send_message(
        ADMIN_ID,
        f"""
💰 THÔNG BÁO NẠP TIỀN

👤 USER: {message.from_user.first_name}
🆔 ID: {user_id}
💵 Số tiền: {amount:,}đ
""",
        reply_markup=markup
    )

    pending_nap[user_id] = {
        "amount": amount,
        "user_msg": msg.message_id,
        "admin_msg": admin_msg.message_id,
        "chat_id": message.chat.id
    }

    def auto_delete():

        time.sleep(900)

        if user_id in pending_nap:

            try:
                bot.delete_message(
                    message.chat.id,
                    msg.message_id
                )
            except:
                pass

            try:
                bot.delete_message(
                    ADMIN_ID,
                    admin_msg.message_id
                )
            except:
                pass

            del pending_nap[user_id]

    threading.Thread(target=auto_delete).start()

# ================= DUYỆT NẠP =================

@bot.callback_query_handler(func=lambda c: c.data.startswith("duyet_"))
def duyet_nap(call):

    data = call.data.split("_")

    user_id = int(data[1])
    amount = int(data[2])

    if user_id not in users:
        users[user_id] = {
            "balance": 0
        }

    users[user_id]["balance"] += amount

    now = datetime.now().strftime("%H:%M:%S %d/%m/%Y")

    if user_id not in nap_history:
        nap_history[user_id] = []

    nap_history[user_id].append({
        "time": now,
        "amount": amount,
        "type": "bank"
    })

    bot.send_message(
        user_id,
        f"""
✅ Nạp tiền thành công

💰 Đã cộng: {amount:,}đ

💳 Số dư:
{users[user_id]['balance']:,}đ
"""
    )

# ================= THUÊ TOOL =================

@bot.callback_query_handler(func=lambda c: c.data == "thuetool")
def thue_tool(call):

    markup = InlineKeyboardMarkup(row_width=1)

    for key, value in TOOLS.items():

        btn = InlineKeyboardButton(
            f"{value[0]} - {value[1]:,}đ",
            callback_data=key
        )

        markup.add(btn)

    bot.send_message(
        call.message.chat.id,
        "🛒 CHỌN TOOL CẦN THUÊ",
        reply_markup=markup
    )

# ================= CHỌN TOOL =================

@bot.callback_query_handler(func=lambda c: c.data in TOOLS)
def chon_tool(call):

    name = TOOLS[call.data][0]
    price = TOOLS[call.data][1]

    markup = InlineKeyboardMarkup(row_width=2)

    ok = InlineKeyboardButton(
        "✅ Xác nhận",
        callback_data=f"buy_{call.data}"
    )

    huy = InlineKeyboardButton(
        "❌ Hủy",
        callback_data="huy"
    )

    markup.add(ok, huy)

    bot.send_message(
        call.message.chat.id,
        f"""
⚠️ Bạn chắc chắn muốn mua:

{name}

💰 Giá: {price:,}đ
""",
        reply_markup=markup
    )

# ================= MUA TOOL =================

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def buy_tool(call):

    user_id = call.from_user.id

    tool_key = call.data.replace("buy_", "")

    name = TOOLS[tool_key][0]
    price = TOOLS[tool_key][1]

    balance = users[user_id]["balance"]

    if balance < price:

        bot.send_message(
            call.message.chat.id,
            f"""
❌ Số dư không đủ

💰 Số dư:
{balance:,}đ
"""
        )
        return

    users[user_id]["balance"] -= price

    now = datetime.now().strftime("%H:%M:%S %d/%m/%Y")

    if user_id not in tool_history:
        tool_history[user_id] = []

    tool_history[user_id].append({
        "time": now,
        "tool": name
    })

    bot.send_message(
        call.message.chat.id,
        f"""
✅ Mua tool thành công

📦 {name}

💰 Đã trừ:
{price:,}đ

💳 Số dư còn:
{users[user_id]['balance']:,}đ
"""
    )

# ================= CÁ NHÂN =================

@bot.callback_query_handler(func=lambda c: c.data == "canhan")
def canhan(call):

    user_id = call.from_user.id

    balance = users[user_id]["balance"]

    markup = InlineKeyboardMarkup(row_width=2)

    btn1 = InlineKeyboardButton(
        "💰 Lịch sử nạp",
        callback_data="lsnap"
    )

    btn2 = InlineKeyboardButton(
        "🛒 Lịch sử tool",
        callback_data="lstool"
    )

    markup.add(btn1, btn2)

    bot.send_message(
        call.message.chat.id,
        f"""
👤 THÔNG TIN CÁ NHÂN

🆔 ID: {user_id}

💰 Số dư:
{balance:,}đ
""",
        reply_markup=markup
    )

# ================= LS NẠP =================

@bot.callback_query_handler(func=lambda c: c.data == "lsnap")
def lsnap(call):

    user_id = call.from_user.id

    if user_id not in nap_history:

        bot.send_message(
            call.message.chat.id,
            "❌ Chưa có lịch sử nạp."
        )
        return

    text = "💰 LỊCH SỬ NẠP TIỀN\n\n"

    data = list(reversed(nap_history[user_id]))

    for i, item in enumerate(data, start=1):

        text += (
            f"{i}. {item['time']} | "
            f"{item['amount']:,} | "
            f"{item['type']}\n"
        )

    bot.send_message(
        call.message.chat.id,
        text
    )

# ================= LS TOOL =================

@bot.callback_query_handler(func=lambda c: c.data == "lstool")
def lstool(call):

    user_id = call.from_user.id

    if user_id not in tool_history:

        bot.send_message(
            call.message.chat.id,
            "❌ Chưa có lịch sử tool."
        )
        return

    text = "🛒 LỊCH SỬ MUA TOOL\n\n"

    data = list(reversed(tool_history[user_id]))

    for i, item in enumerate(data, start=1):

        text += (
            f"{i}. {item['time']} | "
            f"{item['tool']}\n"
        )

    bot.send_message(
        call.message.chat.id,
        text
    )

# ================= BOT TOOL =================

@bot.callback_query_handler(func=lambda c: c.data == "bottool")
def bottool(call):

    bot.send_message(
        call.message.chat.id,
        """
🤖 BOT CHẠY TOOL

📩 Liên hệ:
@luxvipb
"""
    )

# ================= HỦY =================

@bot.callback_query_handler(func=lambda c: c.data == "huy")
def huy(call):

    bot.send_message(
        call.message.chat.id,
        "❌ Đã hủy giao dịch."
    )

print("BOT ĐANG CHẠY...")

bot.infinity_polling()