# eHadir Bot

A Flask-based Telegram bot for daily attendance reminders and self-report logging.

## Routes

- `/` — health check
- `/remind` — send Telegram reminder
- `/start_button` — send self-report inline button
- `/selfreport` — handle button clicks (webhook)

## Setup

1. Replace `BOT_TOKEN` and `CHAT_ID` in `reminder.py` and `selfreport.py`
2. Deploy to Render
3. Set webhook:
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://<your-render-url>/selfreport

4. Schedule cron on Render for `/remind`

## Sample CSV Log

```
user_id, user_name, timestamp
```

## Contact

Developed by Ainie Hayati Noruzman