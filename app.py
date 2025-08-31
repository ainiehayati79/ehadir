from flask import Flask
from reminder import reminder_bp
from selfreport import selfreport_bp
from telegram import Bot

app = Flask(__name__)
app.register_blueprint(reminder_bp)
app.register_blueprint(selfreport_bp)

@app.route("/")
def home():
    return "✅ e-Hadir Bot is running!"

if __name__ == "__main__":
    # Set webhook to Telegram
    bot = Bot(token='7582546703:AAEpBrae4on4d8LglJSqjjI-6LXiGTemZpg')
    bot.set_webhook("https://your-render-app.onrender.com/webhook")

    app.run(host="0.0.0.0", port=5000)
