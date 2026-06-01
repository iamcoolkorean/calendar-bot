import os
import json
import google.generativeai as genai
from datetime import datetime, timedelta

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

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
    text = response.text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())
    
def extract_cancel_info(user_message: str) -> dict:
    today_str = datetime.now().strftime("%Y-%m-%d")
    prompt = f"""
    사용자의 일정 취소 요청을 분석하여 JSON으로 출력하세요.
    오늘 날짜는 {today_str}입니다. 시간대는 Asia/Seoul.
    JSON 형식:
    {{
        "date": "YYYY-MM-DD 형식의 날짜 (예: 2026-06-02). 오늘/내일/모레 같은 상대적 표현은 절대 날짜로 변환.",
        "keyword": "검색할 일정 키워드 (예: 치과)"
    }}
    요청: {user_message}
    """
    response = model.generate_content(prompt)
    text = response.text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())
