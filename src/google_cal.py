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
            calendarId='primary',
            body=event
        ).execute()
        return created['id']
