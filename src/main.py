import os
import re
from datetime import datetime, timedelta
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

# 텔레그램 봇 Application
app = ApplicationBuilder().token(TOKEN).build()

# ──────────────────────────────────────────────
# 텔레그램 MarkdownV2 특수문자 이스케이프
# ──────────────────────────────────────────────
def escape_md(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

# ──────────────────────────────────────────────
# 월간 달력 생성기
# ──────────────────────────────────────────────
def build_calendar_text(year: int, month: int, by_date: dict) -> str:
    import calendar
    cal = calendar.Calendar(firstweekday=6)  # 일요일 시작
    weeks = cal.monthdayscalendar(year, month)

    header = f"📅 {year}년 {month}월"
    days_header = "일   월   화   수   목   금   토"

    lines = []
    for week in weeks:
        week_str = []
        for day in week:
            if day == 0:
                week_str.append("    ")
            else:
                if day in by_date:
                    has_all_day = any(e['all_day'] for e in by_date[day])
                    marker = f"🟢{day:2d}" if has_all_day else f"🟡{day:2d}"
                else:
                    marker = f" {day:2d} "
                week_str.append(marker)
        lines.append(" ".join(week_str))

    summary_lines = []
    for day in sorted(by_date.keys()):
        for e in by_date[day]:
            if e['all_day']:
                summary_lines.append(f"• {day}일 (하루 종일) {e['summary']}")
            else:
                summary_lines.append(f"• {day}일 {e['time']}~{e['end_time']} {e['summary']}")

    result = f"{header}\n{days_header}\n" + "\n".join(lines)
    if summary_lines:
        result += "\n\n📌 일정:\n" + "\n".join(summary_lines)

    return escape_md(result)

# ──────────────────────────────────────────────
# 메시지 핸들러 (모든 자연어 명령 처리)
# ──────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        result = analyze_message(user_text)
    except Exception:
        import traceback
        traceback.print_exc()
        await update.message.reply_text("메시지를 이해할 수 없습니다.")
        return

    intent = result.get("intent")
    params = result.get("params", {})
    gcal = GoogleCalendarManager()

    try:
        # ── 일정 등록 ──
        if intent == "add_event":
            gcal.add_event(params)
            if params.get('all_day', False):
                start = params.get('start_date', '날짜 없음')
                end   = params.get('end_date', start)
                date_msg = f"📅 {start}" if start == end else f"📅 {start} ~ {end}"
                date_msg += " (하루 종일)"
            else:
                start_time = params.get('start_time', '시간 없음')
                end_time   = params.get('end_time', '종료 시간 없음')
                date_msg = f"🕒 {start_time} ~ {end_time}"
            msg = f"📌 {params.get('title', '일정')}\n{date_msg}\n✅ 구글 캘린더에 등록되었습니다."
            await update.message.reply_text(msg)

        # ── 일정 취소 ──
        elif intent == "cancel_event":
            success, msg = gcal.find_and_delete_event(params['date'], params['keyword'])
            await update.message.reply_text(msg)

        # ── 일정 조회 ──
        elif intent == "get_events":
            period = params.get("period", "today")
            today = datetime.now().date()

            if period == "today":
                start = end = today.strftime("%Y-%m-%d")
                events = gcal.list_events_range(start, end)
                if not events:
                    await update.message.reply_text("📅 오늘은 일정이 없습니다.")
                    return
                lines = []
                for e in events:
                    if e['all_day']:
                        lines.append(f"• (하루 종일) {e['summary']}")
                    else:
                        lines.append(f"• {e['time']}~{e['end_time']} {e['summary']}")
                msg = "📅 오늘의 일정\n" + "\n".join(lines)
                await update.message.reply_text(msg)

            elif period == "week":
                start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
                end   = (today + timedelta(days=6 - today.weekday())).strftime("%Y-%m-%d")
                events = gcal.list_events_range(start, end)
                if not events:
                    await update.message.reply_text(f"📅 {start} ~ {end} 일정이 없습니다.")
                    return
                lines = []
                for e in events:
                    day_label = e['date'][-5:]  # "MM-DD"
                    if e['all_day']:
                        lines.append(f"• {day_label} (하루 종일) {e['summary']}")
                    else:
                        lines.append(f"• {day_label} {e['time']}~{e['end_time']} {e['summary']}")
                msg = f"📅 {start} ~ {end} 일정\n" + "\n".join(lines)
                await update.message.reply_text(msg)

            elif period == "month":
                month_param = params.get("month")  # 예: "2026-07"
                if month_param:
                    year  = int(month_param.split("-")[0])
                    month = int(month_param.split("-")[1])
                else:
                    year  = today.year
                    month = today.month
                by_date = gcal.get_monthly_summary(year, month)
                cal_text = build_calendar_text(year, month, by_date)
                await update.message.reply_text(
                    f"```\n{cal_text}\n```", parse_mode="MarkdownV2"
                )
                return
            else:
                await update.message.reply_text("기간을 'today', 'week', 'month'로 말씀해주세요.")

        # ── 일정 수정 ──
        elif intent == "update_event":
            success, msg = gcal.update_event(params['date'], params['keyword'], params)
            await update.message.reply_text(msg)

        else:
            await update.message.reply_text("무엇을 도와드릴까요?")

    except Exception as e:
        import traceback
        traceback.print_exc()
        await update.message.reply_text(f"❌ 오류: {e}")

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ──────────────────────────────────────────────
# Starlette 웹 서버 (Render 웹훅 수신)
# ──────────────────────────────────────────────
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, app.bot)
    await app.process_update(update)
    return JSONResponse({"status": "ok"})

async def health(request: Request):
    return JSONResponse({"status": "alive"})

routes = [
    Route("/telegram", telegram_webhook, methods=["POST"]),
    Route("/health", health, methods=["GET"]),
]

starlette_app = Starlette(routes=routes)

# ──────────────────────────────────────────────
# 서버 시작
# ──────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    service_name = "schedule-bot-2xv2"  # 실제 Render 서비스 이름으로 변경
    webhook_url  = f"https://{service_name}.onrender.com/telegram"

    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(app.initialize())

    async def set_webhook():
        await app.bot.set_webhook(url=webhook_url)
        print(f"Webhook set to {webhook_url}")

    loop.run_until_complete(set_webhook())
    print(f"Starting server on port {port}...")
    uvicorn.run(starlette_app, host="0.0.0.0", port=port, log_level="info")
