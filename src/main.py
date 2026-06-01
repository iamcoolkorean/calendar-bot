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
    
    # Render가 제공하는 PORT 환경변수 (기본 10000)
    port = int(os.environ.get("PORT", 10000))
    # Render 서비스 이름을 반영한 URL (아래 'YOUR_SERVICE_NAME'을 실제 이름으로 변경)
    service_name = "schedule-bot-2xv2"  # 예: "calendar-bot"
    webhook_url = f"https://{service_name}.onrender.com/telegram"
    
    print(f"웹훅 시작: {webhook_url}", flush=True)
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=webhook_url
    )
