from flask import Flask
from telegram import Bot
from reminder import reminder_bp
from selfreport import selfreport_bp

app = Flask(__name__)
app.register_blueprint(reminder_bp)
app.register_blueprint(selfreport_bp)

@app.route("/")
def home():
    return "✅ e-Hadir Bot is running!"

if __name__ == "__main__":
    bot = Bot(token='7582546703:AAEpBrae4on4d8LglJSqjjI-6LXiGTemZpg')
    bot.set_webhook("https://your-render-app.onrender.com/webhook")  # Replace with your actual Render URL
    app.run(host="0.0.0.0", port=5000)