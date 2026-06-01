import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

class GoogleCalendarManager:
    def __init__(self):
        # 단일 사용자(봇 소유자)의 구글 캘린더만 사용
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
            calendarId='primary',
            body=event
        ).execute()
        return created['id']

    def list_events(self, start_date, end_date):
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=start_date.isoformat() + '+09:00',
            timeMax=end_date.isoformat() + '+09:00',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        return [{
            'id': e['id'],
            'summary': e.get('summary', '제목 없음'),
            'start': e['start'].get('dateTime', e['start'].get('date')),
            'end': e['end'].get('dateTime', e['end'].get('date'))
        } for e in events]
