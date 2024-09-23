import datetime
import os.path
from fastapi import UploadFile, File, Form
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main(user : str):
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  print(f"user = {user}.json")
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    print("Getting the upcoming 10 events")
    
    event = {
        "summary": "my test",
        "location": "somewhere in your heart",
        "description": "Som more details",
        "colorId":6,
        "start": {
            "dateTime": "2024-09-22T16:16:16+07:00",
            "timeZone": "Asia/Bangkok"
        },
        "end": {
            "dateTime": "2024-09-22T17:16:16+07:00",
            "timeZone": "Asia/Bangkok"
        }
    }
    
    event = service.events().insert(calendarId="primary", body=event).execute()
    
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("No upcoming events found.")
      return

    # Prints the start and name of the next 10 events
    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))
      print('--------------------------------------------')
      print(start, event["summary"])

  except HttpError as error:
    print(f"An error occurred: {error}")
    
async def upload(file : UploadFile = File(...), user: str = Form(...)):
  contents =await file.read()
  
  with open(f"assets/credentials/{user}.json", 'wb') as f:
    f.write(contents)
    
  return {"filename":'file.filename'}