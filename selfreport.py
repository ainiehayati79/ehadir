from flask import Blueprint, request
import requests
from datetime import datetime
import csv

selfreport_bp = Blueprint('selfreport', __name__)
BOT_TOKEN = 'YOUR_REAL_BOT_TOKEN'
CHAT_ID = 'YOUR_GROUP_CHAT_ID'
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
    return "✅ Self-report handled"

@selfreport_bp.route("/start_button", methods=["GET"])
def start_button():
    keyboard = {
        "inline_keyboard": [[
            {
                "text": "📝 I have self-reported!",
                "callback_data": "self_report"
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