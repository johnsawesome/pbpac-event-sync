import os
import datetime
import os.path
from base64 import b64decode, b64encode
from tempfile import NamedTemporaryFile
from datetime import datetime, timedelta
from typing import Any, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pytz

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.events.owned']
CALENDAR_ID = os.environ['CALENDAR_ID']


if token := os.getenv('TOKEN'):
    with NamedTemporaryFile('wb') as f:
        f.write(b64decode(token.encode('utf-8')))
        f.seek(0)
        creds = Credentials.from_authorized_user_file(f.name)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    # https://developers.google.com/calendar/api/quickstart/python
    service = build('calendar', 'v3', credentials=creds)
else:
    raise Exception()


def get_token(credentials_filename: str):
    flow = InstalledAppFlow.from_client_secrets_file(credentials_filename, SCOPES)
    creds = flow.run_local_server(port=0)
    return b64encode(creds.to_json().encode('utf-8')).decode('utf-8')


def next_n_events(n=100):
    tz = pytz.timezone('America/New_York')
    now = (datetime.now(tz) - timedelta(days=1)).isoformat()
    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=now,
        maxResults=n,
        singleEvents=True,
        orderBy='startTime',
        showDeleted=False,
    ).execute()
    return events_result.get('items', [])


def upsert_event(calendar_id: str, summary: str, start: datetime, end: datetime, description: str, existing_event: Dict[str, Any] | None):
    event = {
        'summary': summary,
        'start': {
            'dateTime': start.strftime('%Y-%m-%dT%H:%M:%S%z'),
            'timeZone': 'America/New_York',  # Explicitly set the timezone to Eastern Time
        },
        'end': {
            'dateTime': end.strftime('%Y-%m-%dT%H:%M:%S%z'),
            'timeZone': 'America/New_York',  # Explicitly set the timezone to Eastern Time
        },
        'reminders': {
            'useDefault': False,
        },
        'extendedProperties': {
            'private': {
                'portlandCalendarId': calendar_id,
            },
        }
    }

    if description:
        event['description'] = description

    if existing_event:
        return service.events().update(calendarId=CALENDAR_ID, eventId=existing_event['id'], body=event).execute()

    return service.events().insert(calendarId=CALENDAR_ID, body=event).execute()

def delete_event(existing_event: Dict[str, Any]):
    service.events().delete(calendarId=CALENDAR_ID, eventId=existing_event['id']).execute()
