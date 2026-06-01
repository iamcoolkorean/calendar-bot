import os
import json
import google.generativeai as genai
from datetime import datetime

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

def analyze_message(user_message: str) -> dict:
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""오늘은 {today_str}. 사용자 메시지를 분석해 아래 JSON만 출력하라.
intent: "add_event", "cancel_event", "get_events", "update_event" 중 하나.
params:
- add_event:
  - 하루 종일: {{"title": "제목", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "all_day": true, "description": "", "location": ""}}
  - 시간: {{"title": "제목", "start_time": "ISO8601", "end_time": "ISO8601", "all_day": false, "description": "", "location": ""}}
- cancel_event: {{"date": "YYYY-MM-DD", "keyword": "검색어"}}
- get_events: {{"period": "today"/"week"/"month"}}
- update_event: {{"date": "YYYY-MM-DD", "keyword": "검색어", "new_title": "새 제목 (없으면 기존 유지)", "new_start_time": "새 ISO8601 시작시간 (없으면 기존 유지)", "new_end_time": "새 ISO8601 종료시간 (없으면 기존 유지)", "new_all_day": true/false (변경 시만 명시)}}

예:
"내일 오후 3시 치과 예약" → {{"intent":"add_event","params":{{"title":"치과 예약","start_time":"2026-06-02T15:00:00+09:00","end_time":"2026-06-02T16:00:00+09:00","all_day":false,"description":"","location":""}}}}
"내일 하루종일 휴가" → {{"intent":"add_event","params":{{"title":"휴가","start_date":"2026-06-02","end_date":"2026-06-02","all_day":true,"description":"","location":""}}}}
"내일 치과 취소" → {{"intent":"cancel_event","params":{{"date":"2026-06-02","keyword":"치과"}}}}
"이번 주 일정" → {{"intent":"get_events","params":{{"period":"week"}}}}
"내일 치과 예약 4시로 바꿔줘" → {{"intent":"update_event","params":{{"date":"2026-06-02","keyword":"치과","new_title":"","new_start_time":"2026-06-02T16:00:00+09:00","new_end_time":"2026-06-02T17:00:00+09:00","new_all_day":false}}}}
"6월 5일 회의 제목 팀 미팅으로 변경" → {{"intent":"update_event","params":{{"date":"2026-06-05","keyword":"회의","new_title":"팀 미팅","new_start_time":"","new_end_time":"","new_all_day":null}}}}

메시지: {user_message}"""
    
    response = model.generate_content(prompt)
    text = response.text.strip()
    
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        text = "\n".join(lines)
    
    return json.loads(text)
