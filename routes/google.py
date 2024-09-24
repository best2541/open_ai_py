from fastapi import APIRouter, Depends, UploadFile, File, Form, Body, Request
from sqlalchemy.orm import Session

from controllers import google, crud
from utilites.database import SessionLocal
from models.google import Token, User, CalendarEvent

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@router.post('/start')
def get_country(request: CalendarEvent, db: Session = Depends(get_db)):
    # datas = crud.get_remind(db, user, google=0, team=0)
    print(type(request.datas))
    print(request.datas[0]['summary'])
    google.main(db, user=request.user, datas=request.datas)
    return 'ok'

@router.post('/upload')
async def upload(file: UploadFile = File(...), user: str = Form(...)):
    result =await google.upload(file,user)
    return result
@router.post('/auth')
def google_auth(token: Token):
    result = google.auth(token)
    return result