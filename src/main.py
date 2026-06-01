import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from src.nlp import extract_event_info, extract_cancel_info
from src.google_cal import GoogleCalendarManager

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def add_event_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """일정 등록"""
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

async def cancel_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """일정 취소"""
    try:
        info = extract_cancel_info(update.message.text)
    except Exception:
        await update.message.reply_text("취소할 일정을 이해할 수 없습니다. 예: '내일 치과 예약 취소해줘'")
        return

    try:
        gcal = GoogleCalendarManager()
        success, msg = gcal.find_and_delete_event(info['date'], info['keyword'])
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ 취소 실패: {e}")

async def today_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """오늘 일정 보기"""
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        gcal = GoogleCalendarManager()
        events = gcal.list_events(today)
        if not events:
            await update.message.reply_text("📅 오늘은 일정이 없습니다.")
            return
        msg = "📅 오늘의 일정:\n" + "\n".join([f"• {e['time']} {e['summary']}" for e in events])
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ 조회 실패: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    
    # 명령어
    app.add_handler(CommandHandler("today", today_events))
    
    # 취소 메시지 (취소/삭제/제거 키워드 포함)
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r'(취소|삭제|제거)'), cancel_event))
    
    # 그 외 메시지는 일정 등록으로 처리
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.Regex(r'(취소|삭제|제거)'), add_event_message))
    
    print("봇 시작 (폴링 모드)")
    app.run_polling()
