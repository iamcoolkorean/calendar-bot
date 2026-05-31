import caldav
from datetime import datetime, timedelta
from src.db import get_user_credentials
from src.utils import decrypt

class NaverCalendarManager:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.client = None

    def _load_credentials(self):
        enc_id, enc_pw = get_user_credentials(self.user_id)
        if not enc_id or not enc_pw:
            raise ValueError("네이버 인증 정보가 없습니다. /set_naver 명령어로 등록하세요.")
        naver_id = decrypt(enc_id)
        app_pw = decrypt(enc_pw)
        return naver_id, app_pw

    def _connect(self):
        naver_id, app_pw = self._load_credentials()
        self.client = caldav.DAVClient(
            url="https://caldav.calendar.naver.com/",
            username=naver_id,
            password=app_pw
        )

    def _get_principal_calendars(self):
        if not self.client:
            self._connect()
        principal = self.client.principal()
        calendars = principal.calendars()
        if not calendars:
            raise Exception("등록된 캘린더가 없습니다.")
        return calendars

    def add_event(self, event_dict: dict):
        calendars = self._get_principal_calendars()
        cal = calendars[0]  # 첫 번째 캘린더 사용
        start = datetime.fromisoformat(event_dict["start_time"])
        end = datetime.fromisoformat(event_dict["end_time"])
        return cal.save_event(
            dtstart=start,
            dtend=end,
            summary=event_dict["title"],
            description=event_dict.get("description", ""),
            location=event_dict.get("location", "")
        )

    def list_events(self, start_date: datetime, end_date: datetime):
        calendars = self._get_principal_calendars()
        cal = calendars[0]
        events = cal.search(start=start_date, end=end_date, event=True, expand=True)
        result = []
        for event in events:
            vevent = event.vobject_instance.vevent
            result.append({
                "uid": vevent.uid.value,
                "summary": vevent.summary.value,
                "start": vevent.dtstart.value.isoformat(),
                "end": vevent.dtend.value.isoformat()
            })
        return result
