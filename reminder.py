from flask import Blueprint
import requests
from datetime import datetime

reminder_bp = Blueprint('reminder', __name__)
BOT_TOKEN = '7582546703:AAEpBrae4on4d8LglJSqjjI-6LXiGTemZpg'
CHAT_ID = '-4983762228'

@reminder_bp.route("/remind", methods=["GET"])
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