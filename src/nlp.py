import os
import json
import google.generativeai as genai
from datetime import datetime

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

def analyze_message(user_message: str) -> dict:
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""오늘은 {today_str}. 사용자 메시지를 분석해 아래 JSON만 출력하라.
intent: "add_event", "cancel_event", "get_events" 중 하나.
params:
- add_event: {{"title": "제목", "start_time": "ISO8601", "end_time": "ISO8601", "all_day": false, "description": "", "location": ""}}
- cancel_event: {{"date": "YYYY-MM-DD", "keyword": "검색어"}}
- get_events: {{"period": "today"/"week"/"month"}}

예:
"내일 오후 3시 치과 예약" → {{"intent":"add_event","params":{{"title":"치과 예약","start_time":"2026-06-02T15:00:00+09:00","end_time":"2026-06-02T16:00:00+09:00","all_day":false,"description":"","location":""}}}}
"내일 치과 취소" → {{"intent":"cancel_event","params":{{"date":"2026-06-02","keyword":"치과"}}}}
"이번 주 일정" → {{"intent":"get_events","params":{{"period":"week"}}}}

메시지: {user_message}"""
    
    response = model.generate_content(prompt)
    text = response.text.strip()
    
    # 코드 블록 제거
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        text = "\n".join(lines)
    
    return json.loads(text)
