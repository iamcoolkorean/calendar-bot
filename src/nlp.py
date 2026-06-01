import os
import json
import google.generativeai as genai
from datetime import datetime

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

def analyze_message(user_message: str) -> dict:
    today_str = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""
오늘 날짜는 {today_str}입니다. 시간대는 Asia/Seoul.
사용자의 메시지를 분석하여 의도(intent)와 필요한 파라미터를 JSON으로 출력하세요.

의도 종류:
- "add_event": 일정 등록. 파라미터: title, start_time (ISO8601), end_time (ISO8601), all_day (boolean), description, location
- "cancel_event": 일정 취소. 파라미터: date (YYYY-MM-DD), keyword (검색어)
- "get_events": 일정 조회. 파라미터: period ("today" 또는 "week" 또는 "month")

사용자 메시지: {user_message}

JSON만 출력하세요.
"""
    response = model.generate_content(prompt)
    text = response.text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())
