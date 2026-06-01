import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from src.nlp import analyze_message
from src.google_cal import GoogleCalendarManager

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        result = analyze_message(user_text)
    except Exception as e:
        await update.message.reply_text("메시지를 이해할 수 없습니다. 다시 말씀해 주세요.")
        return

    intent = result.get("intent")
    params = result.get("params", {})

    try:
        gcal = GoogleCalendarManager()

        if intent == "add_event":
            gcal.add_event(params)
            msg = f"📌 {params.get('title', '일정')}\n🕒 {params.get('start_time', '')} ~ {params.get('end_time', '')}\n✅ 구글 캘린더에 등록되었습니다."
            await update.message.reply_text(msg)

        elif intent == "cancel_event":
            date_str = params.get("date")
            keyword = params.get("keyword")
            if not date_str or not keyword:
                await update.message.reply_text("취소할 일정의 날짜와 키워드를 정확히 말씀해주세요.")
                return
            success, msg = gcal.find_and_delete_event(date_str, keyword)
            await update.message.reply_text(msg)

        elif intent == "get_events":
            period = params.get("period", "today")
            today = datetime.now().date()
            if period == "today":
                start_date = today.strftime("%Y-%m-%d")
                end_date = start_date
            elif period == "week":
                start_of_week = today - timedelta(days=today.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                start_date = start_of_week.strftime("%Y-%m-%d")
                end_date = end_of_week.strftime("%Y-%m-%d")
            elif period == "month":
                start_date = today.replace(day=1).strftime("%Y-%m-%d")
                if today.month == 12:
                    end_of_month = today.replace(year=today.year+1, month=1, day=1) - timedelta(days=1)
                else:
                    end_of_month = today.replace(month=today.month+1, day=1) - timedelta(days=1)
                end_date = end_of_month.strftime("%Y-%m-%d")
            else:
                await update.message.reply_text("조회 기간을 이해할 수 없습니다. '오늘', '이번 주', '이번 달'로 말씀해주세요.")
                return

            events = gcal.list_events_range(start_date, end_date)
            if not events:
                await update.message.reply_text(f"📅 {start_date} ~ {end_date}에 일정이 없습니다.")
                return

            if period == "today":
                header = "📅 오늘의 일정"
                lines = [f"• {e['time']} {e['summary']}" for e in events]
            else:
                header = f"📅 {start_date} ~ {end_date} 일정"
                lines = [f"• {e['date']} {e['time']} {e['summary']}" for e in events]

            msg = header + "\n" + "\n".join(lines)
            await update.message.reply_text(msg)

        else:
            await update.message.reply_text("의도를 파악할 수 없습니다. 일정 등록, 취소, 조회 중 원하는 것을 말씀해주세요.")

    except Exception as e:
        await update.message.reply_text(f"❌ 처리 중 오류 발생: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("봇 시작 (폴링 모드)")
    app.run_polling()
