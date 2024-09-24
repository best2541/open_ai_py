import datetime
import os.path
from models.models import Remind
from sqlalchemy.orm import Session
from fastapi import UploadFile, File, Form
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
from dateutil.parser import *
from controllers import crud

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def main(db:Session, user : str, datas: list[object]):
  print(f"user = {user}.json")
  creds = None
  
  if os.path.exists(f"assets/tokens/{user}.json"):
    creds = Credentials.from_authorized_user_file(f"assets/tokens/{user}.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          f"assets/credentials/{user}.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(f"assets/tokens/{user}.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    print("Getting the upcoming 10 events")
    
    # events = [
    #   {
    #     "summary": "my test",
    #     "location": "somewhere in your heart",
    #     "description": "Som more details",
    #     "colorId":6,
    #     "start": {
    #         "dateTime": "2024-09-24T16:16:16+07:00",
    #         "timeZone": "Asia/Bangkok"
    #     },
    #     "end": {
    #         "dateTime": "2024-09-24T17:16:16+07:00",
    #         "timeZone": "Asia/Bangkok"
    #     }
    # },{
    #     "summary": "my test2",
    #     "location": "somewhere in your heart",
    #     "description": "Som more details",
    #     "colorId":6,
    #     "start": {
    #         "dateTime": "2024-09-25T16:16:16+07:00",
    #         "timeZone": "Asia/Bangkok"
    #     },
    #     "end": {
    #         "dateTime": "2024-09-25T17:16:16+07:00",
    #         "timeZone": "Asia/Bangkok"
    #     }
    # }
    # ]
    
    # # test
    # for data in datas:
    #   print(data.topic)

    # for event in events:
    #   created = service.events().insert(calendarId="primary", body=event).execute()
    #   print(f"Event created : {created.get('htmlLink')}")
    
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
    for data in datas:
      start = data["start"].get("dateTime", data["start"].get("date"))
      print('--------------------------------------------')
      print(start, data['summary'])
      dt = parse(start)
      result = crud.insert_remind(db,user_id=user,topic= data['summary'],date=dt.day,hour=dt.hour,minute=dt.minute)
      print(result)
  except HttpError as error:
    print(f"An error occurred: {error}")
    
async def upload(file : UploadFile = File(...), user: str = Form(...)):
  contents =await file.read()
  
  with open(f"assets/credentials/{user}.json", 'wb') as f:
    f.write(contents)
    
  return {"filename":'file.filename'}

def auth(token:str):
  res = requests.get('https://api.line.me/v2/profile', headers={'Authorization': f"Bearer {token.token}"})
  if (res.status_code == 200):
    return res.json()
  else:
    return {'err': res.status_code, 'detail': res.text}