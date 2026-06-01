import os, sys
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from src.nlp import analyze_message
from src.google_cal import GoogleCalendarManager

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    print(f"[DEBUG] 수신: {user_text}", flush=True)
    try:
        result = analyze_message(user_text)
        print(f"[DEBUG] 분석 결과: {result}", flush=True)
    except Exception:
        import traceback
        traceback.print_exc(file=sys.stderr)
        await update.message.reply_text("메시지를 이해할 수 없습니다.")
        return

    intent = result.get("intent")
    params = result.get("params", {})

    try:
        gcal = GoogleCalendarManager()
        if intent == "add_event":
            gcal.add_event(params)
            await update.message.reply_text(f"✅ {params.get('title')} 등록됨")
        elif intent == "cancel_event":
            ok, msg = gcal.find_and_delete_event(params['date'], params['keyword'])
            await update.message.reply_text(msg)
        elif intent == "get_events":
            from datetime import datetime, timedelta
            period = params.get("period", "today")
            today = datetime.now().date()
            if period == "today":
                start = end = today.strftime("%Y-%m-%d")
            elif period == "week":
                start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
                end = (today + timedelta(days=6-today.weekday())).strftime("%Y-%m-%d")
            elif period == "month":
                start = today.replace(day=1).strftime("%Y-%m-%d")
                if today.month == 12:
                    next_month = today.replace(year=today.year+1, month=1, day=1)
                else:
                    next_month = today.replace(month=today.month+1, day=1)
                end = (next_month - timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                await update.message.reply_text("기간을 'today', 'week', 'month'로 말씀해주세요.")
                return
            events = gcal.list_events_range(start, end)
            if not events:
                await update.message.reply_text(f"📅 {start} ~ {end} 일정 없음")
                return
            msg = "\n".join([f"• {e['date']} {e['time']} {e['summary']}" for e in events])
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("의도를 알 수 없습니다.")
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        await update.message.reply_text(f"❌ 오류: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("봇 시작 (폴링 모드)", flush=True)
    app.run_polling()
