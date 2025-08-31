from flask import Blueprint, request
import requests
from datetime import datetime
import csv

selfreport_bp = Blueprint('selfreport', __name__)

# 🔐 Bot configuration
BOT_TOKEN = '7582546703:AAEpBrae4on4d8LglJSqjjI-6LXiGTemZpg'
CHAT_ID = '-4983762228'
LOG_FILE = 'self_report_log.csv'

@selfreport_bp.route("/selfreport", methods=["POST"])
def self_report():
    data = request.json
    if "callback_query" in data:
        query = data["callback_query"]
        user = query["from"]
        user_id = user["id"]
        user_name = user.get("first_name", "") + " " + user.get("last_name", "")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ✅ Log only if it's the correct user
        if query["data"] == f"self_report:{user_id}":
            with open(LOG_FILE, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([user_id, user_name.strip(), timestamp])

            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
                json={"callback_query_id": query["id"], "text": "✅ Self-report received!"}
            )

            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
                json={
                    "chat_id": query["message"]["chat"]["id"],
                    "message_id": query["message"]["message_id"],
                    "text": f"📝 Thank you {user_name.strip()}, your self-report is logged at {timestamp}."
                }
            )
        else:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
                json={"callback_query_id": query["id"], "text": "⛔ You cannot self-report for others."}
            )

    return "✅ Self-report handled"

@selfreport_bp.route("/start_button", methods=["GET"])
def start_button():
    # 🔘 Button with user-restricted callback
    keyboard = {
        "inline_keyboard": [[
            {
                "text": "📝 I have self-reported!",
                "callback_data": f"self_report:{123456789}"  # Replace with your Telegram user_id or inject dynamically
            }
        ]]
    }
    data = {
        "chat_id": CHAT_ID,
        "text": "Click below to confirm your self-reporting:",
        "reply_markup": keyboard
    }
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(url, json=data)
    return "🟢 Button sent" if response.status_code == 200 else f"❌ Error: {response.text}"
