from flask import Flask
import requests
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = '7582546703:AAEpBrae4on4d8LglJSqjjI-6LXiGTemZpg'  # << your actual bot token here
CHAT_ID = '-4983762228'                     # << your actual chat ID here (include the minus)

@app.route("/")
def home():
    return "e-Hadir Bot is running!"

@app.route("/remind", methods=['GET'])
def send_reminder():
    today = datetime.today().strftime('%d-%m-%Y')

    message = (
        "🔔 *e-Hadir Reminder* (" + today + ")\n\n"
        "✅ Please ensure:\n"
        "- Thumb-in *7:30 to 9.00 AM*\n"
        "- Thumb-out *1 minute before your official end time*\n\n"
        "📎 *e-Hadir record for " + today + "*\n"
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
