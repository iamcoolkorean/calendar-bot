import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from src.db import init_db, save_naver_credentials, user_has_naver_creds
from src.nlp import extract_event_info
from src.naver_cal import NaverCalendarManager

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def set_naver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) != 2:
        await update.message.reply_text("사용법: /set_naver [네이버아이디] [앱비밀번호]")
        return
    naver_id, app_pw = context.args[0], context.args[1]
    save_naver_credentials(user_id, naver_id, app_pw)
    await update.message.reply_text("✅ 네이버 인증 정보가 저장되었습니다.")

async def add_event_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not user_has_naver_creds(user_id):
        await update.message.reply_text("먼저 /set_naver 로 네이버 인증 정보를 등록해주세요.")
        return

    try:
        event = extract_event_info(update.message.text)
    except Exception as e:
        await update.message.reply_text("일정을 이해할 수 없습니다. 다시 말씀해 주세요.")
        return

    try:
        nv = NaverCalendarManager(user_id)
        nv.add_event(event)
        msg = f"📌 {event['title']}\n🕒 {event['start_time']} ~ {event['end_time']}\n✅ 네이버 캘린더에 등록되었습니다."
        await update.message.reply_text(msg)
    except ValueError as e:
        await update.message.reply_text(str(e))
    except Exception as e:
        await update.message.reply_text(f"❌ 등록 실패: {e}")

async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not user_has_naver_creds(user_id):
        await update.message.reply_text("/set_naver 먼저!")
        return
    nv = NaverCalendarManager(user_id)
    now = datetime.now()
    events = nv.list_events(now, now + timedelta(days=7))
    if not events:
        await update.message.reply_text("이번 주 일정이 없습니다.")
        return
    msg = "\n".join([f"• {e['start']} {e['summary']}" for e in events])
    await update.message.reply_text(f"📅 이번 주 일정:\n{msg}")

if __name__ == "__main__":
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("set_naver", set_naver))
    app.add_handler(CommandHandler("events", events))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_message))
    
    # 개발 단계에서는 폴링, 배포 시 웹훅으로 전환
    print("봇 시작 (폴링 모드)")
    app.run_polling()
