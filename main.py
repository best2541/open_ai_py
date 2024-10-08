from fastapi import FastAPI, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes.chat import router as chat_router
from routes.users import router as users_router
from routes.setting import router as setting_router
from routes.static import router as static_router
from routes.google import router as google_router
from typing import Dict, Any
from controllers import crud
from sqlalchemy.orm import Session
from utilites.database import SessionLocal

# Create all tables
# from models import Base
# Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
app = FastAPI()

load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include the router
app.include_router(users_router, prefix="/users")
app.include_router(chat_router, prefix='/chat')
app.include_router(setting_router, prefix='/setting')
app.include_router(static_router, prefix='/static')
app.mount("/static", StaticFiles(directory="templates"), name="static")
app.include_router(google_router, prefix='/google')

# Initialize the Jinja2Templates object
templates = Jinja2Templates(directory="templates")

@app.get('/webhook')
def test():
    return 'ok'
@app.post('/webhook')
def oh(db: Session = Depends(get_db)):
    result = crud.get_log(db=db, user_id='random')
    return result
@app.get('/')
def getStatus():
    return "OK"
@app.post('/')
def post(item:Dict[str,Any], db: Session = Depends(get_db)):
    crud.test(db=db,item=item)
    return 'result'
