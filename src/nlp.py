import os
import json
import google.generativeai as genai
from datetime import datetime

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

def analyze_message(user_message: str) -> dict:
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
당신은 일정 관리 비서입니다. 사용자의 한국어 메시지를 분석하여 아래 JSON 형식으로만 응답하세요. 다른 말은 절대 하지 마세요.

JSON 형식:
{{"intent": "<의도>", "params": {{...}}}}

<의도> 종류와 params 설명:
1. "add_event": 새 일정 등록
   params: {{
       "title": "일정 제목 (문자열)",
       "start_time": "ISO8601 시작시간 (예: 2026-06-02T15:00:00+09:00)",
       "end_time": "ISO8601 종료시간 (시작+1시간으로 추정)",
       "all_day": false (기본값 false),
       "description": "추가 내용 (없으면 빈 문자열)",
       "location": "장소 (없으면 빈 문자열)"
   }}
2. "cancel_event": 일정 취소
   params: {{
       "date": "YYYY-MM-DD 형식의 날짜",
       "keyword": "취소할 일정의 검색 키워드 (예: 치과, 미팅 등)"
   }}
3. "get_events": 일정 조회
   params: {{
       "period": "today" 또는 "week" 또는 "month" 중 하나
   }}

오늘 날짜는 {today_str}입니다. 시간대는 Asia/Seoul입니다. "내일", "다음 주 월요일" 같은 상대적 표현은 절대 날짜로 변환하세요. 시작 시간만 언급된 경우 종료 시간은 1시간 뒤로 설정하세요.

아래는 예시입니다:

예시1:
사용자: 내일 오후 3시 치과 예약
응답: {{"intent": "add_event", "params": {{"title": "치과 예약", "start_time": "2026-06-02T15:00:00+09:00", "end_time": "2026-06-02T16:00:00+09:00", "all_day": false, "description": "", "location": ""}}}}

예시2:
사용자: 6월 5일 오전 10시 팀 미팅 추가해줘
응답: {{"intent": "add_event", "params": {{"title": "팀 미팅", "start_time": "2026-06-05T10:00:00+09:00", "end_time": "2026-06-05T11:00:00+09:00", "all_day": false, "description": "", "location": ""}}}}

예시3:
사용자: 내일 치과 예약 취소해줘
응답: {{"intent": "cancel_event", "params": {{"date": "2026-06-02", "keyword": "치과"}}}}

예시4:
사용자: 오늘 병원 제거
응답: {{"intent": "cancel_event", "params": {{"date": "{today_str}", "keyword": "병원"}}}}

예시5:
사용자: 오늘 일정 알려줘
응답: {{"intent": "get_events", "params": {{"period": "today"}}}}

예시6:
사용자: 이번 주 일정 뭐 있어?
응답: {{"intent": "get_events", "params": {{"period": "week"}}}}

예시7:
사용자: 이번 달 일정 보여줘
응답: {{"intent": "get_events", "params": {{"period": "month"}}}}

이제 아래 사용자 메시지를 분석하여 JSON만 출력하세요.
사용자 메시지: {user_message}
"""
    
    response = model.generate_content(prompt)
    text = response.text.strip()
    
    # 코드 블록 마크다운 제거
    if text.startswith("```"):
        lines = text.split("\n")
        # 첫 줄 (```json) 제거, 마지막 줄 (```) 제거
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    
    return json.loads(text)
