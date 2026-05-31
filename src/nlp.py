import os
import json
import google.generativeai as genai
from datetime import datetime, timedelta

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')  # 최신 모델

def extract_event_info(user_message: str) -> dict:
    today_str = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""
    오늘 날짜는 {today_str}입니다. 시간대는 Asia/Seoul.
    사용자의 일정 등록 요청을 분석하여 JSON으로 출력하세요.
    JSON 형식:
    {{
        "title": "일정 제목",
        "start_time": "ISO8601 datetime (예: 2026-06-01T14:00:00+09:00)",
        "end_time": "ISO8601 datetime (시작+1시간으로 추정)",
        "all_day": false,
        "description": "상세 내용",
        "location": "장소"
    }}
    요청: {user_message}
    """
    response = model.generate_content(prompt)
    # JSON 부분만 추출
    text = response.text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())
