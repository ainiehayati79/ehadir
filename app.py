from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
import csv
import os
import logging
import asyncio
import threading
import time

# === Configuration ===
BOT_TOKEN = '7582546703:AAEpBrae4on4d8LglJSqjjI-6LXiGTemZpg'
LOG_FILE = 'self_report_log.csv'

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Bot
bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# Global event loop for async operations
loop = None
loop_thread = None

# Track last reminder dates (daily, not hourly)
last_morning_date = ""
last_afternoon_date = ""

def start_background_loop():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_forever()

def run_in_background_loop(coro):
    global loop, loop_thread
    if loop is None or loop_thread is None or not loop_thread.is_alive():
        loop_thread = threading.Thread(target=start_background_loop, daemon=True)
        loop_thread.start()
        time.sleep(0.1)
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=30)

def initialize_csv():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['User ID', 'Full Name', 'Timestamp'])

# === FIXED: Private chat only ===
async def handle_selfreport_command(update):
    try:
        # Check if this is a private chat (not a group)
        if update.effective_chat.type != 'private':
            logger.info(f"Ignoring /selfreport command in group chat: {update.effective_chat.id}")
            return
        
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
        logger.info(f"Selfreport command handled for user {update.effective_user.full_name} in private chat")
    except Exception as e:
        logger.error(f"Error in selfreport command: {e}")

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

    # Get Malaysia time
    malaysia_time = datetime.utcnow() + timedelta(hours=8)
    timestamp = malaysia_time.strftime("%Y-%m-%d %H:%M:%S")
    
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

async def process_update(update):
    try:
        if update.message and update.message.text == '/selfreport':
            await handle_selfreport_command(update)
        elif update.callback_query:
            await handle_callback_query(update)
    except Exception as e:
        logger.error(f"Error processing update: {e}")

# === WEBHOOKS ===
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        json_data = request.get_json(force=True)
        if json_data:
            update = Update.de_json(json_data, bot)
            run_in_background_loop(process_update(update))
            return jsonify({"status": "ok"})
        else:
            return jsonify({"status": "error", "message": "No JSON data"}), 400
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# === FIXED: Daily morning reminder ===
@app.route("/cron/remind", methods=["GET"])
def cron_remind():
    global last_morning_date
    try:
        malaysia_time = datetime.utcnow() + timedelta(hours=8)
        today = malaysia_time.strftime('%Y-%m-%d')
        
        # Prevent duplicates - only allow 1 reminder per DAY
        if today == last_morning_date:
            return "SKIP"
        
        today_display = malaysia_time.strftime('%d-%m-%Y')
        current_time = malaysia_time.strftime('%H:%M')
        
        message = (
            f"🔔 e-HADIR MORNING REMINDER 🔔\n"
            f"📅 {today_display} | ⏰ {current_time}\n\n"
            f"✅ Thumb-in: 7:30-9:00 AM\n"
            f"🤖 Machine down? Use /selfreport\n"
            f"🎯 Start your day right!"
        )
        
        run_in_background_loop(
            bot.send_message(
                chat_id='-4983762228', 
                text=message, 
                parse_mode="Markdown"
            )
        )
        
        last_morning_date = today
        return "OK"
    except Exception as e:
        logger.error(f"Morning reminder error: {e}")
        return "FAIL"

# === FIXED: Daily afternoon reminder ===
@app.route("/cron/afternoon", methods=["GET"])
def cron_afternoon():
    global last_afternoon_date
    try:
        malaysia_time = datetime.utcnow() + timedelta(hours=8)
        today = malaysia_time.strftime('%Y-%m-%d')
        
        # Prevent duplicates - only allow 1 reminder per DAY
        if today == last_afternoon_date:
            return "SKIP"
        
        today_display = malaysia_time.strftime('%d-%m-%Y')
        current_time = malaysia_time.strftime('%H:%M')
        
        message = (
            f"⏰ THUMB-OUT REMINDER ⏰\n"
            f"📅 {today_display} | ⏰ {current_time}\n\n"
            f"📋 Check PDF below for thumb-in times\n"
            f"🧮 Formula: Thumb-in + 9 hours\n"
            f"⚠️ Complete 8 hours before leaving!"
        )
        
        run_in_background_loop(send_afternoon_reminder_with_pdf(message))
        last_afternoon_date = today
        return "OK"
    except Exception as e:
        logger.error(f"Afternoon reminder error: {e}")
        return "FAIL"

async def send_afternoon_reminder_with_pdf(message):
    try:
        await bot.send_message(
            chat_id='-4983762228',
            text=message,
            parse_mode="Markdown"
        )
        
        malaysia_time = datetime.utcnow() + timedelta(hours=8)
        pdf_filename = f"ehadir_{malaysia_time.strftime('%Y-%m-%d')}.pdf"
        
        if os.path.exists(pdf_filename):
            with open(pdf_filename, 'rb') as pdf_file:
                await bot.send_document(
                    chat_id='-4983762228',
                    document=pdf_file,
                    caption=f"📋 Today's attendance - {malaysia_time.strftime('%d/%m/%Y')}"
                )
        else:
            await bot.send_message(
                chat_id='-4983762228',
                text="📋 PDF not available - contact HR"
            )
    except Exception as e:
        logger.error(f"Error sending afternoon reminder: {e}")

# === PDF UPLOAD ===
@app.route("/upload/pdf", methods=["POST"])
def upload_daily_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '' or not file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "Please upload a PDF file"}), 400
        
        malaysia_time = datetime.utcnow() + timedelta(hours=8)
        filename = f"ehadir_{malaysia_time.strftime('%Y-%m-%d')}.pdf"
        file.save(filename)
        
        return jsonify({
            "status": "PDF uploaded successfully",
            "filename": filename,
            "size": f"{os.path.getsize(filename)} bytes"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/upload", methods=["GET"])
def upload_form():
    return '''
    <html><body>
        <h2>Upload Today's e-Hadir PDF</h2>
        <form method="POST" action="/upload/pdf" enctype="multipart/form-data">
            <input type="file" name="file" accept=".pdf" required>
            <input type="submit" value="Upload PDF">
        </form>
    </body></html>
    '''

# === OTHER ROUTES ===
@app.route("/")
def home():
    return jsonify({
        "status": "e-Hadir Bot Running",
        "version": "3.0 - Clean & Fixed",
        "endpoints": ["/logs", "/dashboard", "/upload", "/export"]
    })

@app.route("/logs", methods=["GET"])
def view_logs():
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
        return jsonify({"error": str(e)}), 500

@app.route("/export", methods=["GET"])
def export_csv():
    try:
        if os.path.exists(LOG_FILE):
            return send_file(LOG_FILE, 
                           mimetype='text/csv',
                           as_attachment=True,
                           download_name='ehadir_backup.csv')
        else:
            return "No data available", 404
    except Exception as e:
        return f"Error: {str(e)}", 500

# === START APP ===
if __name__ == "__main__":
    initialize_csv()
    
    webhook_url = "https://ehadir.onrender.com/webhook"
    try:
        result = run_in_background_loop(bot.set_webhook(webhook_url))
        if result:
            logger.info(f"✅ Webhook set successfully")
        else:
            logger.error("❌ Failed to set webhook")
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
    
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Starting e-Hadir Bot on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
