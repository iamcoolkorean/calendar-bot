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

app = ApplicationBuilder().token(TOKEN).build()


def escape_md(text: str) -> str:
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


def to_short_date(iso_date: str) -> str:
    """YYYY-MM-DD → MM/DD (연도 제거)"""
    try:
        dt = datetime.strptime(iso_date, "%Y-%m-%d")
        return f"{dt.month}/{dt.day}"
    except ValueError:
        return iso_date


def format_all_day_range(e: dict) -> str:
    """종일 일정의 날짜 범위를 간결하게 표시 (예: 6/20, 7/15~16)"""
    start = to_short_date(e['date'])
    if e.get('end_date') and e['date'] != e['end_date']:
        end = to_short_date(e['end_date'])
        # 같은 달이면 뒷부분은 일만 표시
        if e['date'][:7] == e['end_date'][:7]:
            end_short = e['end_date'].split('-')[2]  # "DD"
            return f"{start}~{end_short}"
        else:
            return f"{start}~{end}"
    return start


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
                real_end = (datetime.strptime(end, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
                # 표시용 변환
                start_short = to_short_date(start)
                if real_end == start:
                    date_msg = f"📅 {start_short} (하루 종일)"
                else:
                    # 기간일 때 간결하게
                    if start[:7] == real_end[:7]:
                        end_short = real_end.split('-')[2]
                        date_msg = f"📅 {start_short}~{end_short} (하루 종일)"
                    else:
                        date_msg = f"📅 {start_short}~{to_short_date(real_end)} (하루 종일)"
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
                        range_str = format_all_day_range(e)
                        lines.append(f"• {range_str} (하루 종일) {e['summary']}")
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
                    if e['all_day']:
                        range_str = format_all_day_range(e)
                        lines.append(f"• {range_str} (하루 종일) {e['summary']}")
                    else:
                        day_label = to_short_date(e['date'])
                        lines.append(f"• {day_label} {e['time']}~{e['end_time']} {e['summary']}")
                msg = f"📅 {start} ~ {end} 일정\n" + "\n".join(lines)
                await update.message.reply_text(msg)

            elif period == "month":
                month_param = params.get("month")
                if month_param:
                    year  = int(month_param.split("-")[0])
                    month = int(month_param.split("-")[1])
                else:
                    year  = today.year
                    month = today.month

                import calendar as cal_mod
                last_day = cal_mod.monthrange(year, month)[1]
                start = f"{year}-{month:02d}-01"
                end   = f"{year}-{month:02d}-{last_day:02d}"

                events = gcal.list_events_range(start, end)
                if not events:
                    await update.message.reply_text(f"📅 {start} ~ {end} 일정이 없습니다.")
                    return
                lines = []
                for e in events:
                    if e['all_day']:
                        range_str = format_all_day_range(e)
                        lines.append(f"• {range_str} (하루 종일) {e['summary']}")
                    else:
                        day_label = to_short_date(e['date'])
                        lines.append(f"• {day_label} {e['time']}~{e['end_time']} {e['summary']}")
                msg = f"📅 {start} ~ {end} 일정\n" + "\n".join(lines)
                await update.message.reply_text(msg)
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


# 웹 서버
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    service_name = "schedule-bot-2xv2"
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
