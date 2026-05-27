# Telegram Shop Bot (pyTelegramBotAPI)

## Cài đặt local
```bash
pip install -r requirements.txt
export BOT_TOKEN=xxx
export ADMIN_IDS=123456789
python bot.py
```

## Deploy Railway
1. Push code lên GitHub.
2. Railway → New Project → Deploy from GitHub.
3. Variables:
   - `BOT_TOKEN` = token BotFather
   - `ADMIN_IDS` = ID admin (cách nhau dấu phẩy)
   - `DB_PATH` = `/data/shop.db` (gắn Volume `/data` để giữ DB)
4. Settings → Start Command: `python bot.py` (đã có Procfile worker).

## Lệnh chính
- `/start` – mở menu
- `/naptien <số tiền>` – tạo QR VietQR
- `/admin` – panel admin

## Cấu hình
Sửa thông tin ngân hàng và link VietQR trong `bot.py`:
- `VIETQR_IMAGE`
- `BANK_NAME`, `BANK_ACCOUNT`, `BANK_HOLDER`
