
import caldav
from datetime import datetime, timedelta
from typing import Dict, Optional
import json
from cryptography.fernet import Fernet
import os

# 서버 시작 시 한 번 생성되는 암호화 키 (환경변수에서 로드)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
fernet = Fernet(ENCRYPTION_KEY) if ENCRYPTION_KEY else None

class NaverCalendarManager:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.client = None

    def _load_credentials(self) -> tuple:
        """DB에서 복호화된 네이버 아이디/앱 비밀번호 반환"""
        from db import get_user_credentials
        enc_id, enc_pw = get_user_credentials(self.user_id)  # DB에서 암호문 조회
        if not enc_id or not enc_pw:
            raise ValueError("네이버 인증 정보가 없습니다. /set_naver 명령어로 등록하세요.")
        naver_id = fernet.decrypt(enc_id.encode()).decode()
        app_pw = fernet.decrypt(enc_pw.encode()).decode()
        return naver_id, app_pw

    def _connect(self):
        if self.client:
            return
        naver_id, app_pw = self._load_credentials()
        self.client = caldav.DAVClient(
            url="https://caldav.calendar.naver.com/",
            username=naver_id,
            password=app_pw
        )

    def _get_principal_calendars(self):
        self._connect()
        principal = self.client.principal()
        calendars = principal.calendars()
        if not calendars:
            raise Exception("등록된 캘린더가 없습니다.")
        return calendars

    def add_event(self, event_dict: Dict) -> str:
        """event_dict: title, start_time, end_time, description, location"""
        calendars = self._get_principal_calendars()
        # 기본으로 첫 번째 캘린더 사용. 특정 캘린더를 원하면 이름으로 검색 가능.
        cal = calendars[0]  
        start = datetime.fromisoformat(event_dict["start_time"])
        end = datetime.fromisoformat(event_dict["end_time"])
        # 네이버 CalDAV는 dtstart/dtend가 datetime 객체여야 함
        event = cal.save_event(
            dtstart=start,
            dtend=end,
            summary=event_dict["title"],
            description=event_dict.get("description", ""),
            location=event_dict.get("location", "")
        )
        # 생성된 이벤트의 URL 추출
        return str(event.url)

    def list_events(self, start_date: datetime, end_date: datetime) -> list:
        """특정 기간 일정 조회"""
        calendars = self._get_principal_calendars()
        cal = calendars[0]
        events = cal.search(
            start=start_date,
            end=end_date,
            event=True,
            expand=True
        )
        result = []
        for event in events:
            vevent = event.vobject_instance.vevent
            result.append({
                "uid": vevent.uid.value,
                "summary": vevent.summary.value,
                "dtstart": vevent.dtstart.value.isoformat(),
                "dtend": vevent.dtend.value.isoformat(),
            })
        return result
