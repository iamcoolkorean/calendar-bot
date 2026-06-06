import os
from datetime import datetime, timedelta
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

    # ──────────────────────────────
    # 이벤트 추가 (종일 end_date 보정 포함)
    # ──────────────────────────────
    def add_event(self, event_dict: dict):
        event = {
            'summary': event_dict['title'],
            'description': event_dict.get('description', ''),
            'location': event_dict.get('location', ''),
        }
        if event_dict.get('all_day', False):
            start = event_dict['start_date']
            end   = event_dict['end_date']
            # end_date는 exclusive여야 하므로, 만약 start보다 작거나 같으면 start + 1로 보정
            if end <= start:
                end = (datetime.strptime(start, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            event['start'] = {'date': start, 'timeZone': 'Asia/Seoul'}
            event['end']   = {'date': end,   'timeZone': 'Asia/Seoul'}
        else:
            event['start'] = {'dateTime': event_dict['start_time'], 'timeZone': 'Asia/Seoul'}
            event['end']   = {'dateTime': event_dict['end_time'],   'timeZone': 'Asia/Seoul'}

        created = self.service.events().insert(calendarId='primary', body=event).execute()
        return created['id']

    # ──────────────────────────────
    # 기간 조회 (종일 일정 종료일 보정 포함)
    # ──────────────────────────────
    def list_events_range(self, start_date: str, end_date: str):
        start = f"{start_date}T00:00:00+09:00"
        end   = f"{end_date}T23:59:59+09:00"
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
            start_info = e['start'].get('dateTime', e['start'].get('date'))
            end_info   = e['end'].get('dateTime', e['end'].get('date'))

            if 'dateTime' in e['start']:
                # ── 시간 일정 ──
                all_day = False
                date_str = start_info[:10]
                time_str = start_info[11:16]
                end_time_str = end_info[11:16]
                start_date_str = date_str
                end_date_str = date_str
            else:
                # ── 종일 일정 ──
                all_day = True
                # exclusive end → 실제 종료일은 end_date의 하루 전
                real_end = (datetime.strptime(end_info, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
                start_date_str = start_info
                end_date_str = real_end
                time_str = '하루종일'
                end_time_str = ''

            result.append({
                'id': e['id'],
                'summary': summary,
                'date': start_date_str,
                'end_date': end_date_str,          # 실제 종료일
                'time': time_str,
                'end_time': end_time_str,
                'all_day': all_day
            })
        return result

    # ──────────────────────────────
    # 월별 요약 (날짜별 그룹)
    # ──────────────────────────────
    def get_monthly_summary(self, year: int, month: int) -> dict:
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        start_date = f"{year}-{month:02d}-01"
        end_date   = f"{year}-{month:02d}-{last_day:02d}"
        events = self.list_events_range(start_date, end_date) or []
        by_date = {}
        for e in events:
            day = int(e['date'].split('-')[2])
            by_date.setdefault(day, []).append(e)
        return by_date

    # ──────────────────────────────
    # 이벤트 검색
    # ──────────────────────────────
    def find_event(self, date_str: str, keyword: str):
        start = f"{date_str}T00:00:00+09:00"
        end   = f"{date_str}T23:59:59+09:00"
        events_result = self.service.events().list(
            calendarId='primary', timeMin=start, timeMax=end,
            q=keyword, singleEvents=True
        ).execute()
        items = events_result.get('items', [])
        return items[0] if items else None

    # ──────────────────────────────
    # 이벤트 삭제
    # ──────────────────────────────
    def find_and_delete_event(self, date_str: str, keyword: str):
        event = self.find_event(date_str, keyword)
        if not event:
            return False, f"'{date_str}'에 '{keyword}' 관련 일정을 찾을 수 없습니다."
        self.service.events().delete(calendarId='primary', eventId=event['id']).execute()
        return True, f"✅ '{event.get('summary', '일정')}' 일정이 취소되었습니다."

    # ──────────────────────────────
    # 이벤트 수정
    # ──────────────────────────────
    def update_event(self, date_str: str, keyword: str, updates: dict):
        event = self.find_event(date_str, keyword)
        if not event:
            return False, f"'{date_str}'에 '{keyword}' 관련 일정을 찾을 수 없습니다."

        body = {}
        if updates.get('new_title'):
            body['summary'] = updates['new_title']

        # 종일 ↔ 시간 전환 또는 날짜/시간 변경
        if updates.get('new_all_day') is True:
            body['start'] = {'date': updates.get('new_start_date', date_str), 'timeZone': 'Asia/Seoul'}
            body['end']   = {'date': updates.get('new_end_date', date_str), 'timeZone': 'Asia/Seoul'}
        elif updates.get('new_all_day') is False:
            if updates.get('new_start_time'):
                body['start'] = {'dateTime': updates['new_start_time'], 'timeZone': 'Asia/Seoul'}
                body['end']   = {'dateTime': updates.get('new_end_time', ''), 'timeZone': 'Asia/Seoul'}
        else:
            if updates.get('new_start_date'):
                body['start'] = {'date': updates['new_start_date'], 'timeZone': 'Asia/Seoul'}
                body['end']   = {'date': updates.get('new_end_date', updates['new_start_date']), 'timeZone': 'Asia/Seoul'}
            elif updates.get('new_start_time'):
                body['start'] = {'dateTime': updates['new_start_time'], 'timeZone': 'Asia/Seoul'}
                body['end']   = {'dateTime': updates.get('new_end_time', ''), 'timeZone': 'Asia/Seoul'}

        if body:
            self.service.events().patch(calendarId='primary', eventId=event['id'], body=body).execute()
            return True, f"✅ '{event.get('summary', '일정')}' 일정이 수정되었습니다."
        else:
            return False, "수정할 내용이 없습니다."
