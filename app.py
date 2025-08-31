from flask import Flask, request
import requests
from datetime import datetime
import csv

app = Flask(__name__)

# 🔐 Replace with your real bot token and group chat ID
BOT_TOKEN = '7582546703:AAEpBrae4on4d8LglJSqjjI-6LXiGTemZpg'  # << your actual bot token here
CHAT_ID = '-4983762228'                     # << your actual chat ID here (include the minus)

# 📂 Log file
LOG_FILE = 'self_report_log.csv'

# 🏠 Health check
@app.route("/")
def home():
    return "e-Hadir Bot is running!"

# 🔔 Reminder sender (for cron job)
@app.route("/remind", methods=['GET'])
def send_reminder():
    today = datetime.today().strftime('%d-%m-%Y')

    message = (
        f"🔔 *e-Hadir Reminder* ({today})\n\n"
        "✅ Please ensure:\n"
        "- Thumb-in *7:30 to 9.00 AM*\n"
        "- Thumb-out *1 minute before your official end time*\n\n"
        f"📎 *e-Hadir record for {today}*\n"
        "Let's maintain full compliance ✔"
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    response = requests.post(url, data=data)
    return "✅ Reminder sent" if response.status_code == 200 else f"❌ Error: {response.text}"


# 📝 Self-report webhook
@app.route("/selfreport", methods=['POST'])
def self_report():
    data = request.json

    if "callback_query" in data:
        query = data["callback_query"]
        user = query["from"]
        user_id = user["id"]
        user_name = user.get("first_name", "") + " " + user.get("last_name", "")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 💾 Log report
        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([user_id, user_name.strip(), timestamp])

        # ✅ Acknowledge the button press
        callback_id = query["id"]
        reply_text = f"📝 Thank you {user_name.strip()}, your self-report is logged at {timestamp}."

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
            json={"callback_query_id": callback_id, "text": "✅ Self-report received!"}
        )

        # ✏️ Edit message to avoid repeat click
        message = query["message"]
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText",
            json={
                "chat_id": message["chat"]["id"],
                "message_id": message["message_id"],
                "text": reply_text
            }
        )

    return "✅ Self-report handled"


# 👆 Start self-report inline button manually
@app.route("/start_button", methods=['GET'])
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
    return "🟢 Self-report button sent" if response.status_code == 200 else f"❌ Error: {response.text}"


if __name__ == "__main__":
    app.run(debug=True)
