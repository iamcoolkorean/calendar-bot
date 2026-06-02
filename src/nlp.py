import os
import json
import time
import google.generativeai as genai
from datetime import datetime

# 8개의 API 키 (GitHub 시크릿 또는 Render 환경 변수에 등록)
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

# None이 아닌 키만 필터링
API_KEYS = [key for key in API_KEYS if key]

# 사용할 모델 (할당량이 넉넉한 모델로 설정)
MODEL_NAME = 'gemini-2.5-flash'

# 현재 사용 중인 키 인덱스
current_key_index = 0

def get_model():
    """현재 API 키로 모델 생성"""
    if not API_KEYS:
        raise ValueError("사용 가능한 Gemini API 키가 없습니다.")
    key = API_KEYS[current_key_index]
    genai.configure(api_key=key)
    return genai.GenerativeModel(MODEL_NAME)

def switch_to_next_key():
    """할당량 초과 시 다음 API 키로 전환"""
    global current_key_index
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    print(f"[INFO] API 키 전환: {current_key_index + 1}번 키 사용 중")

def safe_json_parse(text: str) -> dict:
    """Gemini의 불완전한 JSON 응답을 보정"""
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
        text = text[start_idx:end_idx+1]

    return json.loads(text)

def analyze_message(user_message: str) -> dict:
    """사용자 메시지 분석 (할당량 초과 시 자동으로 키 전환)"""
    global current_key_index
    
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

메시지: {user_message}"""

    # 최대 API 키 개수만큼 재시도
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
                print(f"[WARN] 키 {current_key_index + 1} 할당량 초과. 다음 키로 전환...")
                switch_to_next_key()
                time.sleep(1)  # 잠시 대기 후 재시도
            else:
                # 할당량 초과가 아닌 다른 오류는 그대로 전파
                raise

    # 모든 키가 소진된 경우
    raise RuntimeError("모든 Gemini API 키의 할당량이 초과되었습니다. 잠시 후 다시 시도해주세요.")
