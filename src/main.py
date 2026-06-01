import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from src.nlp import extract_event_info
from src.google_cal import GoogleCalendarManager

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def add_event_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        event = extract_event_info(update.message.text)
    except Exception:
        await update.message.reply_text("일정을 이해할 수 없습니다. 다시 말씀해 주세요.")
        return

    try:
        gcal = GoogleCalendarManager()
        gcal.add_event(event)
        msg = f"📌 {event['title']}\n🕒 {event['start_time']} ~ {event['end_time']}\n✅ 구글 캘린더에 등록되었습니다."
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ 등록 실패: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_message))
    print("봇 시작 (폴링 모드)")
    app.run_polling()
