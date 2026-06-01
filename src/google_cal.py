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
            calendarId='primary', body=event
        ).execute()
        return created['id']

    def list_events_range(self, start_date: str, end_date: str):
        start = f"{start_date}T00:00:00+09:00"
        end = f"{end_date}T23:59:59+09:00"
        events_result = self.service.events().list(
            calendarId='primary', timeMin=start, timeMax=end,
            singleEvents=True, orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        if not events:
            return None
        result = []
        for e in events:
            summary = e.get('summary', '제목 없음')
            start_time = e['start'].get('dateTime', e['start'].get('date'))
            date_str = start_time.split('T')[0] if 'T' in start_time else start_time
            time_str = start_time.split('T')[1][:5] if 'T' in start_time else '하루종일'
            result.append({
                'id': e['id'],
                'summary': summary,
                'date': date_str,
                'time': time_str
            })
        return result

    def find_and_delete_event(self, date_str: str, keyword: str):
        start = f"{date_str}T00:00:00+09:00"
        end = f"{date_str}T23:59:59+09:00"
        events_result = self.service.events().list(
            calendarId='primary', timeMin=start, timeMax=end,
            q=keyword, singleEvents=True
        ).execute()
        items = events_result.get('items', [])
        if not items:
            return False, f"'{date_str}'에 '{keyword}' 관련 일정을 찾을 수 없습니다."
        event = items[0]
        self.service.events().delete(
            calendarId='primary', eventId=event['id']
        ).execute()
        return True, f"✅ '{event.get('summary', '일정')}' 일정이 취소되었습니다."
