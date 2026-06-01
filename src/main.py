import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from src.nlp import extract_event_info
from src.google_cal import GoogleCalendarManager

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def add_event_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        event = extract_event_info(update.message.text)
    except Exception as e:
        import traceback
        traceback.print_exc()
        await update.message.reply_text("일정을 이해할 수 없습니다. 다시 말씀해 주세요.")
        return

    try:
        gcal = GoogleCalendarManager()
        gcal.add_event(event)
        msg = f"📌 {event['title']}\n🕒 {event['start_time']} ~ {event['end_time']}\n✅ 구글 캘린더에 등록되었습니다."
        await update.message.reply_text(msg)
    except Exception as e:
        import traceback
        traceback.print_exc()
        await update.message.reply_text(f"❌ 등록 실패: {e}")

async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gcal = GoogleCalendarManager()
    now = datetime.now()
    items = gcal.list_events(now, now + timedelta(days=7))
    if not items:
        await update.message.reply_text("이번 주 일정이 없습니다.")
        return
    msg = "\n".join([f"• {e['start']} {e['summary']}" for e in items])
    await update.message.reply_text(f"📅 이번 주 일정:\n{msg}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("events", events))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_message))
    print("봇 시작 (폴링 모드)")
    app.run_polling()
