from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler
import csv
from datetime import datetime

# === Configuration ===
BOT_TOKEN = '7582546703:AAEpBrae4on4d8LglJSqjjI-6LXiGTemZpg'
LOG_FILE = 'self_report_log.csv'
bot = Bot(token=BOT_TOKEN)

# === Flask App ===
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, workers=1, use_context=True)

# === /selfreport Command ===
def start(update, context):
    user_id = update.effective_user.id
    keyboard = [[
        InlineKeyboardButton(
            "📝 I have self-reported!",
            callback_data=f'self_report:{user_id}'
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Click below to confirm your self-reporting:", reply_markup=reply_markup)

# === Callback Button Handler ===
def button_handler(update, context):
    query = update.callback_query
    user = query.from_user
    data = query.data

    try:
        action, allowed_user_id = data.split(':')
        allowed_user_id = int(allowed_user_id)
    except ValueError:
        query.answer("⚠ Invalid button data.", show_alert=True)
        return

    if user.id != allowed_user_id:
        query.answer("⛔ You cannot self-report for someone else.", show_alert=True)
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([user.id, user.full_name, timestamp])

    query.answer("✅ Self-report received!")
    query.edit_message_text(text=f"📝 Thank you {user.full_name}, your self-report is logged at {timestamp}.")

# === Register Handlers ===
dispatcher.add_handler(CommandHandler("selfreport", start))
dispatcher.add_handler(CallbackQueryHandler(button_handler))

# === Telegram Webhook Endpoint ===
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "✅ Webhook handled"

# === Health Check ===
@app.route("/")
def home():
    return "e-Hadir Webhook Bot is running."

# === Start App ===
if __name__ == "__main__":
    bot.set_webhook("https://ehadir.onrender.com/webhook")  # Replace with your actual Render URL
    app.run(host="0.0.0.0", port=5000)