import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

class GoogleCalendarManager:
    def __init__(self):
        self.service = self._get_service()

    def _get_service(self):
        creds = Credentials(
            token=None,
            refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=SCOPES
        )
        return build('calendar', 'v3', credentials=creds)
def list_events(self, date_str: str):
    """특정 날짜의 일정 목록 반환"""
    start = f"{date_str}T00:00:00+09:00"
    end = f"{date_str}T23:59:59+09:00"
    events_result = self.service.events().list(
        calendarId='primary',
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    if not events:
        return None
    result = []
    for e in events:
        summary = e.get('summary', '제목 없음')
        start_time = e['start'].get('dateTime', e['start'].get('date'))
        # 시간만 추출
        if 'T' in start_time:
            time_str = start_time.split('T')[1][:5]
        else:
            time_str = '하루종일'
        result.append({
            'id': e['id'],
            'summary': summary,
            'time': time_str
        })
    return result

def find_and_delete_event(self, date_str: str, keyword: str):
    """키워드로 일정 찾아서 삭제"""
    start = f"{date_str}T00:00:00+09:00"
    end = f"{date_str}T23:59:59+09:00"
    events_result = self.service.events().list(
        calendarId='primary',
        timeMin=start,
        timeMax=end,
        q=keyword,
        singleEvents=True
    ).execute()
    
    items = events_result.get('items', [])
    if not items:
        return False, f"'{date_str}'에 '{keyword}' 관련 일정을 찾을 수 없습니다."
    
    # 첫 번째 매칭된 일정 삭제
    event = items[0]
    self.service.events().delete(
        calendarId='primary',
        eventId=event['id']
    ).execute()
    return True, f"✅ '{event.get('summary', '일정')}' 일정이 취소되었습니다."
    def add_event(self, event_dict: dict):
        event = {
            'summary': event_dict['title'],
            'start': {
                'dateTime': event_dict['start_time'],
                'timeZone': 'Asia/Seoul',
            },
            'end': {
                'dateTime': event_dict['end_time'],
                'timeZone': 'Asia/Seoul',
            },
            'description': event_dict.get('description', ''),
            'location': event_dict.get('location', ''),
        }
        created = self.service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        return created['id']
