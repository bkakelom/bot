import asyncio
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from pycryptopay import CryptoPay

# === Configuration ===
USD_TO_ETB_RATE = 160
CRYPTO_API_KEY = "421237:AAKyMEUxbKZEOX8AMsGcq4KxANonI6zv0dZ"
TELEGRAM_BOT_TOKEN = "8196544626:AAHHL28e3a_xLFwbwkQt7cBlLnh1xRi0Mo8"
PAID_URL = "https://t.me/goldhuntaz_bot"

# === Initialize CryptoPay ===
crypto = CryptoPay(api_key=CRYPTO_API_KEY)

def convert_to_etb(usd_amount):
    return usd_amount * USD_TO_ETB_RATE

async def get_payment_menu(plan_label, back_callback, usd_amount):
    etb_amount = convert_to_etb(usd_amount)
    try:
        invoice = await crypto.create_invoice(
            asset="USDT",
            amount=usd_amount,
            description=f"Gold Hunta – {plan_label.replace('_', ' ').title()}",
            paid_btn_name="OPEN_BOT",
            paid_btn_url=PAID_URL
        )
        url = invoice.pay_url
        crypto_button = InlineKeyboardButton(f"💎 Pay with Crypto (${usd_amount})", url=url)
    except Exception as e:
        print(f"[Crypto Error] {e}")
        crypto_button = InlineKeyboardButton("💎 Pay with Crypto (Unavailable)", callback_data="crypto_error")

    return InlineKeyboardMarkup([
        [crypto_button],
        [InlineKeyboardButton(f"🏦 Pay with CBE ({etb_amount} ETB)", callback_data=f"pay_cbe_{plan_label}_{usd_amount}")],
        [InlineKeyboardButton("⬅️ Back", callback_data=back_callback)]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Reset reply keyboard (restart-like behavior)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="♻️ Restarting Gold Hunta bot...",
        reply_markup=ReplyKeyboardRemove()
    )

    keyboard = [
        [InlineKeyboardButton("VIP Signal Room", callback_data="vip_menu")],
        [InlineKeyboardButton("1-to-1 Mentorship", callback_data="mentorship_menu")],
        [InlineKeyboardButton("Forex Master Class", callback_data="forex_class")],
    ]
    message_text = (
        "👋 *Welcome to Gold Hunta — where smart trading begins!*\n\n"
        "Explore our exclusive offerings:\n"
        "🔸 VIP Signal Room\n"
        "🔸 1-to-1 Mentorship\n"
        "🔸 Forex Master Class\n\n"
        "Tap a category below to view plans and secure your edge in the market ⬇:"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Navigation only — preserves any existing reply keyboards
    keyboard = [
        [InlineKeyboardButton("VIP Signal Room", callback_data="vip_menu")],
        [InlineKeyboardButton("1-to-1 Mentorship", callback_data="mentorship_menu")],
        [InlineKeyboardButton("Forex Master Class", callback_data="forex_class")],
    ]
    message_text = (
        "👋 *Main Menu*\n\n"
        "Choose a service below to explore plans ⬇️"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cb = query.data

    try:
        if cb == "vip_menu":
            buttons = [
                [InlineKeyboardButton("🗓️ 1 Month", callback_data="vip_1 Month_10")],
                [InlineKeyboardButton("🗓️ 3 Months", callback_data="vip_3 Month_25")],
                [InlineKeyboardButton("🗓️ 6 Months", callback_data="vip_6 Month_50")],
                [InlineKeyboardButton("⬅️ Back", callback_data="main")]
            ]
            await query.edit_message_text(
                "*📊 VIP Signal Room Plans:*\nHigh accuracy gold signals, real-time alerts, and strategy insights.\n\nChoose a plan ⬇️",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode="Markdown"
            )

        elif cb == "mentorship_menu":
            buttons = [
                [InlineKeyboardButton("🧠 Monthly", callback_data="mentorship_1 Month_100")],
                [InlineKeyboardButton("📈 3-Month Plan", callback_data="mentorship_3 Month Growth Plan_250")],
                [InlineKeyboardButton("⬅️ Back", callback_data="main")]
            ]
            await query.edit_message_text(
                "*🎯 1-to-1 Mentorship:*\nPersonalized coaching, trading mindset, and full access to VIP signals.\n\nSelect your package ⬇️",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode="Markdown"
            )

        elif cb == "forex_class":
            await query.edit_message_text(
                "📚 *Forex Master Class*\n\nComing soon! Stay tuned for our immersive education platform.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]]),
                parse_mode="Markdown"
            )

        elif cb.startswith("vip_") or cb.startswith("mentorship_"):
            parts = cb.split("_")
            if len(parts) >= 3:
                plan_type = parts[0]
                duration = parts[1]
                usd_amount = int(parts[2])
                readable = "VIP Signal Room" if plan_type == "vip" else "1-to-1 Mentorship"
                menu_markup = await get_payment_menu(f"{plan_type}_{duration}", f"{plan_type}_menu", usd_amount)
                await query.edit_message_text(
                    f"*{readable} — {duration.replace('1 Month', 'Monthly').replace('3 Month', '3-Month Plan')}*\n"
                    f"💰 ${usd_amount} = {convert_to_etb(usd_amount)} ETB\n\nChoose your payment option 👇",
                    reply_markup=menu_markup,
                    parse_mode="Markdown"
                )

        elif cb.startswith("pay_cbe_"):
            parts = cb.split("_")
            if len(parts) >= 4:
                plan_type = parts[2]
                duration = parts[3]
                usd_amount = int(parts[4])
                etb_amount = convert_to_etb(usd_amount)
                label = "VIP Signal Room" if "vip" in plan_type else "1-to-1 Mentorship"
                readable = duration.replace('1 Month', 'Monthly').replace('3 Month', '3-Month Plan')
                msg = (
                    f"🏦 *{label} – {readable}*\n\n"
                    f"💵 {etb_amount} ETB (≈ ${usd_amount})\n"
                    "🏛 Commercial Bank of Ethiopia\n"
                    "👤 Bereket Akelom\n"
                    "🔢 1000266592438\n\n"
                    "📸 After payment, send receipt to [@huntazsupport](https://t.me/huntazsupport)."
                )
                back_callback = "vip_menu" if "vip" in plan_type else "mentorship_menu"
                await query.edit_message_text(
                    msg,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=back_callback)]]),
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )

        elif cb == "main":
            await menu(update, context)

        elif cb == "crypto_error":
            await query.answer("⚠️ Crypto invoice unavailable. Try again later.", show_alert=True)

    except Exception as e:
        print(f"[Callback Error] {e}")
        await query.answer("Something went wrong. Please try again.")

# === Bot Entry Point ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("🚀 Bot is running...")
    app.run_polling()
