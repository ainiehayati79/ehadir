from flask import Flask, request, jsonify
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import csv
import os
from datetime import datetime
import logging
import asyncio

# === Configuration ===
BOT_TOKEN = '7582546703:AAEpBrae4on4d8LglJSqjjI-6LXiGTemZpg'
LOG_FILE = 'self_report_log.csv'

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Initialize Bot and Application ===
application = Application.builder().token(BOT_TOKEN).build()

# === Flask App ===
app = Flask(__name__)

# === Create CSV file with headers if it doesn't exist ===
def initialize_csv():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['User ID', 'Full Name', 'Timestamp'])

# === /selfreport Command ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        keyboard = [[
            InlineKeyboardButton(
                "📝 I have self-reported!",
                callback_data=f'self_report:{user_id}'
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Click below to confirm your self-reporting:", 
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")

# === Callback Button Handler ===
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    data = query.data

    try:
        action, allowed_user_id = data.split(':')
        allowed_user_id = int(allowed_user_id)
    except ValueError:
        await query.answer("⚠ Invalid button data.", show_alert=True)
        return

    if user.id != allowed_user_id:
        await query.answer("⛔ You cannot self-report for someone else.", show_alert=True)
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Log to CSV
    try:
        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([user.id, user.full_name, timestamp])
        
        await query.answer("✅ Self-report received!")
        await query.edit_message_text(
            text=f"📝 Thank you {user.full_name}, your self-report is logged at {timestamp}."
        )
        logger.info(f"Self-report logged for user {user.full_name} ({user.id}) at {timestamp}")
        
    except Exception as e:
        logger.error(f"Error logging self-report: {e}")
        await query.answer("❌ Error logging self-report. Please try again.", show_alert=True)

# === Register Handlers ===
application.add_handler(CommandHandler("selfreport", start))
application.add_handler(CallbackQueryHandler(button_handler))

# === Async helper function ===
def run_async(coro):
    """Helper function to run async code in sync context"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# === Telegram Webhook Endpoint ===
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        json_data = request.get_json(force=True)
        if json_data:
            update = Update.de_json(json_data, application.bot)
            
            # Process update in async context
            run_async(application.process_update(update))
            
            return jsonify({"status": "ok"})
        else:
            return jsonify({"status": "error", "message": "No JSON data"}), 400
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/remind", methods=["GET"])
def send_reminder():
    try:
        today = datetime.today().strftime('%d-%m-%Y')
        message = (
            f"🔔 *e-Hadir Reminder* ({today})\n\n"
            "✅ Please ensure:\n"
            "- Thumb-in *7:30 to 9.00 AM*\n"
            "- Thumb-out *1 minute before your official end time*\n\n"
            f"📎 *e-Hadir record for {today}*\n"
            "Let's maintain full compliance ✔"
        )
        
        # Send message asynchronously
        run_async(
            application.bot.send_message(
                chat_id='-4983762228', 
                text=message, 
                parse_mode="Markdown"
            )
        )
        
        logger.info("Reminder sent successfully")
        return jsonify({"status": "Reminder sent successfully"})
        
    except Exception as e:
        logger.error(f"Reminder error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# === Health Check ===
@app.route("/")
def home():
    return jsonify({
        "status": "e-Hadir Webhook Bot is running",
        "version": "2.0",
        "python_telegram_bot": "20.7"
    })

@app.route("/logs", methods=["GET"])
def view_logs():
    """Endpoint to view recent self-report logs"""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                logs = list(reader)
                return jsonify({
                    "total_entries": len(logs) - 1,  # Exclude header
                    "recent_logs": logs[-10:]  # Return last 10 entries
                })
        else:
            return jsonify({"logs": [], "total_entries": 0})
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# === Start App ===
if __name__ == "__main__":
    # Initialize CSV file
    initialize_csv()
    
    # Set webhook
    webhook_url = "https://ehadir.onrender.com/webhook"  # Replace with your actual URL
    try:
        result = run_async(application.bot.set_webhook(webhook_url))
        if result:
            logger.info(f"✅ Webhook set successfully to: {webhook_url}")
        else:
            logger.error("❌ Failed to set webhook")
    except Exception as e:
        logger.error(f"❌ Failed to set webhook: {e}")
    
    # Start Flask app
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
