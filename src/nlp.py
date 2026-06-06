import os
import json
import time
import google.generativeai as genai
from datetime import datetime

# ──────────────────────────────────────────────
# 8개의 Gemini API 키 로테이션
# ──────────────────────────────────────────────
API_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
    os.getenv("GEMINI_API_KEY_5"),
    os.getenv("GEMINI_API_KEY_6"),
    os.getenv("GEMINI_API_KEY_7"),
    os.getenv("GEMINI_API_KEY_8"),
]
API_KEYS = [key for key in API_KEYS if key]

MODEL_NAME = 'gemini-2.5-flash'
current_key_index = 0


def get_model():
    if not API_KEYS:
        raise ValueError("사용 가능한 Gemini API 키가 없습니다.")
    key = API_KEYS[current_key_index]
    genai.configure(api_key=key)
    return genai.GenerativeModel(MODEL_NAME)


def switch_to_next_key():
    global current_key_index
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    print(f"[INFO] API 키 전환 → {current_key_index + 1}번 키")


def safe_json_parse(text: str) -> dict:
    if text.startswith("```"):
        lines = text.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)

    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx != -1 and end_idx != -1:
        text = text[start_idx:end_idx + 1]

    return json.loads(text)


def analyze_message(user_message: str) -> dict:
    global current_key_index
    today_str = datetime.now().strftime("%Y-%m-%d")
    current_year = datetime.now().strftime("%Y")

    prompt = f"""오늘은 {today_str}. 연도는 생략될 수 있으며, 생략 시 현재 연도({current_year})로 가정한다.
사용자 메시지를 분석해 아래 JSON만 출력하라.
intent: "add_event", "cancel_event", "get_events", "update_event" 중 하나.
params:
- add_event:
  - 종일: {{"title": "제목", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD (종료 다음날!)", "all_day": true, "description": "", "location": ""}}
    *중요*: 종일 이벤트는 end_date가 exclusive이므로 실제 종료일의 다음 날을 입력할 것.
    예) 6/17~19 → start_date: {current_year}-06-17, end_date: {current_year}-06-20
  - 시간: {{"title": "제목", "start_time": "ISO8601", "end_time": "ISO8601", "all_day": false, "description": "", "location": ""}}
- cancel_event: {{"date": "YYYY-MM-DD", "keyword": "검색어"}}
- get_events: {{"period": "today"/"week"/"month", "month": "YYYY-MM (특정 월인 경우만 명시, 없으면 현재 월)"}}
- update_event: {{"date": "YYYY-MM-DD", "keyword": "검색어", "new_title": "", "new_start_time": "", "new_end_time": "", "new_start_date": "", "new_end_date": "", "new_all_day": true/false/null}}

예시:
"6/4 오후 3시 치과 예약" → {{"intent":"add_event","params":{{"title":"치과 예약","start_time":"{current_year}-06-04T15:00:00+09:00","end_time":"{current_year}-06-04T16:00:00+09:00","all_day":false,"description":"","location":""}}}}
"6/17~19 휴가" → {{"intent":"add_event","params":{{"title":"휴가","start_date":"{current_year}-06-17","end_date":"{current_year}-06-20","all_day":true,"description":"","location":""}}}}
"6/4 치과 취소" → {{"intent":"cancel_event","params":{{"date":"{current_year}-06-04","keyword":"치과"}}}}
"이번 주 일정" → {{"intent":"get_events","params":{{"period":"week"}}}}
"7월 일정" → {{"intent":"get_events","params":{{"period":"month","month":"{current_year}-07"}}}}
"6/4 치과 4시로 변경" → {{"intent":"update_event","params":{{"date":"{current_year}-06-04","keyword":"치과","new_title":"","new_start_time":"{current_year}-06-04T16:00:00+09:00","new_end_time":"{current_year}-06-04T17:00:00+09:00","new_start_date":"","new_end_date":"","new_all_day":false}}}}

메시지: {user_message}"""

    max_retries = len(API_KEYS)
    for attempt in range(max_retries):
        try:
            model = get_model()
            response = model.generate_content(prompt)
            text = response.text.strip()
            return safe_json_parse(text)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                print(f"[WARN] 키 {current_key_index + 1} 할당량 초과")
                switch_to_next_key()
                time.sleep(1)
            else:
                raise

    raise RuntimeError("모든 API 키의 할당량이 초과되었습니다.")
