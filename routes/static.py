from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from controllers import crud
from utilites.database import SessionLocal
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# Route to render HTML
@router.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    with open('templates/google.html') as f:
        return HTMLResponse(content=f.read())

@router.get('/calendar')
def get_calendar():
    return 'test'