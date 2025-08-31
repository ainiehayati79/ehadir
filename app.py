from flask import Flask
from reminder import reminder_bp
from selfreport import selfreport_bp

app = Flask(__name__)
app.register_blueprint(reminder_bp)
app.register_blueprint(selfreport_bp)

@app.route("/")
def home():
    return "✅ e-Hadir Bot is running!"

if __name__ == "__main__":
    app.run(debug=True)