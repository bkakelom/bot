import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from pycryptopay import CryptoPay
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CRYPTO_API_TOKEN = os.getenv("CRYPTO_API_TOKEN")
BOT_URL = os.getenv("BOT_URL")
USD_TO_ETB_RATE = 160

crypto = CryptoPay(api_token=CRYPTO_API_TOKEN, network="mainnet")

def convert_to_etb(usd_amount):
    return usd_amount * USD_TO_ETB_RATE

def get_payment_menu(plan_label, back_callback, usd_amount):
    etb_amount = convert_to_etb(usd_amount)
    try:
        invoice = crypto.create_invoice(
            asset="USDT",
            amount=usd_amount,
            description=f"Gold Hunta – {plan_label.replace('_', ' ').title()}",
            paid_btn_name="OPEN_BOT",
            paid_btn_url="https://t.me/your_bot"
        )
        url = invoice['result']['bot_invoice_url']
        crypto_button = InlineKeyboardButton(f"💰 Pay with Crypto (${usd_amount})", url=url)
    except Exception as e:
        print(f"[Crypto Error] {e}")
        crypto_button = InlineKeyboardButton("💰 Pay with Crypto (Unavailable)", callback_data="crypto_error")

    return InlineKeyboardMarkup([
        [crypto_button],
        [InlineKeyboardButton(f"🏦 Pay with CBE ({etb_amount} ETB)", callback_data=f"pay_cbe_{plan_label}_{usd_amount}")],
        [InlineKeyboardButton("⬅️ Back", callback_data=back_callback)]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("VIP Signal Room", callback_data="vip_menu")],
        [InlineKeyboardButton("1-to-1 Mentorship", callback_data="mentorship_menu")],
        [InlineKeyboardButton("Forex Master Class", callback_data="forex_class")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 *Welcome to Gold Hunta!*", reply_markup=reply_markup, parse_mode="Markdown")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cb = query.data
    try:
        if cb == "vip_menu":
            buttons = [
                [InlineKeyboardButton("🗓️ 1 Month", callback_data="vip_1m_10")],
                [InlineKeyboardButton("🗓️ 3 Months", callback_data="vip_3m_25")],
                [InlineKeyboardButton("🗓️ 6 Months", callback_data="vip_6m_50")],
                [InlineKeyboardButton("⬅️ Back", callback_data="main")]
            ]
            await query.edit_message_text("*📊 VIP Signal Room Plans:*", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        elif cb == "mentorship_menu":
            buttons = [
                [InlineKeyboardButton("🧠 Monthly", callback_data="mentorship_1m_100")],
                [InlineKeyboardButton("📈 3-Month Plan", callback_data="mentorship_3m_250")],
                [InlineKeyboardButton("⬅️ Back", callback_data="main")]
            ]
            await query.edit_message_text("*🎯 1-to-1 Mentorship Options:*", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        elif cb == "forex_class":
            await query.edit_message_text("📚 *Forex Master Class*
Launching soon!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="main")]]), parse_mode="Markdown")
        elif cb.startswith("vip_") or cb.startswith("mentorship_"):
            parts = cb.split("_")
            if len(parts) >= 3:
                plan_type, duration, usd_amount = parts[0], parts[1], int(parts[2])
                readable = "VIP Signal Room" if plan_type == "vip" else "1-to-1 Mentorship"
                await query.edit_message_text(
                    f"*{readable} – {duration.replace('1m', 'Monthly').replace('3m', '3-Month Plan')}*
Price: ${usd_amount}/{convert_to_etb(usd_amount)} ETB",
                    reply_markup=get_payment_menu(f"{plan_type}_{duration}", f"{plan_type}_menu", usd_amount),
                    parse_mode="Markdown"
                )
        elif cb.startswith("pay_cbe_"):
            parts = cb.split("_")
            if len(parts) >= 4:
                plan_type, duration, usd_amount = parts[2], parts[3], int(parts[4])
                etb_amount = convert_to_etb(usd_amount)
                msg = f"🏦 *Pay {etb_amount} ETB (${usd_amount}) to:*\nBank: CBE\nName: Bereket Akelom\nAccount: 1000266592438\nSend proof to [@huntazsupport](https://t.me/huntazsupport)"
                back_callback = "vip_menu" if "vip" in plan_type else "mentorship_menu"
                await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=back_callback)]]), parse_mode="Markdown", disable_web_page_preview=True)
        elif cb == "main":
            await start(update, context)
        elif cb == "crypto_error":
            await query.answer("⚠️ Crypto invoice unavailable. Try later.", show_alert=True)
    except Exception as e:
        print(f"[Callback Error] {e}")
        await query.answer("Something went wrong. Try again.")

@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return "OK"

if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.run_webhook(listen="0.0.0.0", port=8080, webhook_url=f"{BOT_URL}/")