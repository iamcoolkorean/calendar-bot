import os
import sys
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from src.nlp import analyze_message
from src.google_cal import GoogleCalendarManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# 텔레그램 봇 Application 생성
app = ApplicationBuilder().token(TOKEN).build()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        result = analyze_message(user_text)
    except Exception:
        await update.message.reply_text("메시지를 이해할 수 없습니다.")
        return

    intent = result.get("intent")
    params = result.get("params", {})
    gcal = GoogleCalendarManager()

    try:
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
                await update.message.reply_text("기간을 오늘/주/월 중에 말씀해주세요.")
                return
            events = gcal.list_events_range(start, end)
            if not events:
                await update.message.reply_text("일정이 없습니다.")
                return
            msg = "\n".join([f"• {e['date']} {e['time']} {e['summary']}" for e in events])
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("무엇을 도와드릴까요?")
    except Exception as e:
        await update.message.reply_text(f"❌ 오류: {e}")

# 핸들러 등록
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# 웹훅을 처리할 Starlette 엔드포인트
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, app.bot)
    await app.process_update(update)
    return JSONResponse({"status": "ok"})

# 상태 확인용 (Render 포트 감지 통과)
async def health(request: Request):
    return JSONResponse({"status": "alive"})

routes = [
    Route("/telegram", telegram_webhook, methods=["POST"]),
    Route("/health", health, methods=["GET"]),
]

starlette_app = Starlette(routes=routes)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    service_name = "schedule-bot-2xv2"
    webhook_url = f"https://{service_name}.onrender.com/telegram"

    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Application 초기화 (이 한 줄이 핵심!)
    loop.run_until_complete(app.initialize())

    async def set_webhook():
        await app.bot.set_webhook(url=webhook_url)
        print(f"Webhook set to {webhook_url}")

    loop.run_until_complete(set_webhook())
    
    print(f"Starting server on port {port}...")
    uvicorn.run(starlette_app, host="0.0.0.0", port=port, log_level="info")
