from datetime import timedelta
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def add_to_calendar(user, outfits_with_details):
    if not user.google_refresh_token:
        return False
    creds = Credentials(
        token=None,
        refresh_token=user.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    )
    try:
        service = build("calendar", "v3", credentials=creds)

        for item in outfits_with_details:
            date_object = item["date"]
            current_date = str(date_object)
            next_date = str(date_object + timedelta(days=1))
            t_min = f"{current_date}T00:00:00Z"
            t_max = f"{current_date}T23:59:59Z"
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=t_min,
                    timeMax=t_max,
                    singleEvents=True,
                )
                .execute()
            )
            events = events_result.get("items", [])
            for event in events:
                event_date = event.get("start", {}).get("date")
                if event_date == current_date and event.get("summary", "").startswith(
                    "Outfit:"
                ):
                    service.events().delete(
                        calendarId="primary", eventId=event["id"]
                    ).execute()
            new_event = {
                "summary": f"Outfit: {item['top']} + {item['bottom']}",
                "description": "Outfit recommendation for the day",
                "start": {"date": str(item["date"])},
                "end": {"date": str(next_date)},
            }
            service.events().insert(calendarId="primary", body=new_event).execute()
        return True
    except Exception as e:
        print(f"Calendar Sync Error: {e}")
        return False
