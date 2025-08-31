from flask import Flask
from selfreport import selfreport_bp
from reminder import reminder_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(selfreport_bp)
app.register_blueprint(reminder_bp)

@app.route("/")
def home():
    return "✅ e-Hadir Bot is running!"

if __name__ == "__main__":
    app.run(debug=True)
