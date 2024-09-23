from fastapi import APIRouter, Depends, UploadFile, File, Form, Body
from sqlalchemy.orm import Session

from controllers import google
from utilites.database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@router.post('/start')
def get_country(user: str =Body(...)):
    google.main(user)
    return 'ok'

@router.post('/upload')
async def upload(file: UploadFile = File(...), user: str = Form(...)):
    result =await google.upload(file,user)
    return result