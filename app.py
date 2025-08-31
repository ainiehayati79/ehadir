from flask import Flask, request, jsonify
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
import csv
import os
from datetime import datetime
import logging
import asyncio
import threading
from functools import wraps

# === Configuration ===
BOT_TOKEN = '7582546703:AAEpBrae4on4d8LglJSqjjI-6LXiGTemZpg'
LOG_FILE = 'self_report_log.csv'

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Initialize Bot ===
bot = Bot(token=BOT_TOKEN)

# === Flask App ===
app = Flask(__name__)

# === Global event loop for async operations ===
loop = None
loop_thread = None

def start_background_loop():
    """Start event loop in background thread"""
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_forever()

def run_in_background_loop(coro):
    """Run coroutine in background event loop"""
    global loop, loop_thread
    
    if loop is None or loop_thread is None or not loop_thread.is_alive():
        loop_thread = threading.Thread(target=start_background_loop, daemon=True)
        loop_thread.start()
        # Give the thread time to start
        import time
        time.sleep(0.1)
    
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=30)  # 30 second timeout

# === Create CSV file with headers if it doesn't exist ===
def initialize_csv():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['User ID', 'Full Name', 'Timestamp'])

# === /selfreport Command Handler ===
async def handle_selfreport_command(update):
    try:
        user_id = update.effective_user.id
        keyboard = [[
            InlineKeyboardButton(
                "📝 I have self-reported!",
                callback_data=f'self_report:{user_id}'
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.send_message(
            chat_id=update.effective_chat.id,
            text="Click below to confirm your self-reporting:",
            reply_markup=reply_markup
        )
        logger.info(f"Selfreport command handled for user {update.effective_user.full_name}")
    except Exception as e:
        logger.error(f"Error in selfreport command: {e}")

# === Callback Button Handler ===
async def handle_callback_query(update):
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

# === Process Update Function ===
async def process_update(update):
    try:
        # Handle /selfreport command
        if update.message and update.message.text == '/selfreport':
            await handle_selfreport_command(update)
        
        # Handle callback queries (button presses)
        elif update.callback_query:
            await handle_callback_query(update)
            
    except Exception as e:
        logger.error(f"Error processing update: {e}")

# === Telegram Webhook Endpoint ===
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        json_data = request.get_json(force=True)
        if json_data:
            update = Update.de_json(json_data, bot)
            
            # Process update in background loop
            run_in_background_loop(process_update(update))
            
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
        
        # Send message in background loop
        run_in_background_loop(
            bot.send_message(
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
        "version": "2.2 - Fixed Async",
        "python_telegram_bot": "20.3",
        "loop_status": "active" if loop and not loop.is_closed() else "inactive"
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
                    "total_entries": len(logs) - 1 if len(logs) > 0 else 0,
                    "recent_logs": logs[-10:] if len(logs) > 0 else []
                })
        else:
            return jsonify({"logs": [], "total_entries": 0})
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/test", methods=["GET"])
def test_bot():
    """Test endpoint to check if bot is working"""
    try:
        # Get bot info in background loop
        bot_info = run_in_background_loop(bot.get_me())
        return jsonify({
            "status": "Bot is working",
            "bot_name": bot_info.first_name,
            "bot_username": bot_info.username,
            "bot_id": bot_info.id
        })
    except Exception as e:
        logger.error(f"Bot test error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/webhook_info", methods=["GET"])
def webhook_info():
    """Get current webhook information"""
    try:
        webhook_info = run_in_background_loop(bot.get_webhook_info())
        return jsonify({
            "url": webhook_info.url,
            "has_custom_certificate": webhook_info.has_custom_certificate,
            "pending_update_count": webhook_info.pending_update_count,
            "last_error_date": webhook_info.last_error_date,
            "last_error_message": webhook_info.last_error_message,
            "max_connections": webhook_info.max_connections,
            "allowed_updates": webhook_info.allowed_updates
        })
    except Exception as e:
        logger.error(f"Webhook info error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# === Start App ===
if __name__ == "__main__":
    # Initialize CSV file
    initialize_csv()
    
    # Start background event loop
    logger.info("Starting background event loop...")
    
    # Set webhook
    webhook_url = "https://ehadir.onrender.com/webhook"
    try:
        result = run_in_background_loop(bot.set_webhook(webhook_url))
        if result:
            logger.info(f"✅ Webhook set successfully to: {webhook_url}")
        else:
            logger.error("❌ Failed to set webhook")
    except Exception as e:
        logger.error(f"❌ Failed to set webhook: {e}")
    
    # Start Flask app
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Starting Flask app on port {port} (Fixed Async)")
    app.run(host="0.0.0.0", port=port, debug=False)
