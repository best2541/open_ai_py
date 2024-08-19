from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes.chat import router
from routes.users import router as users_router
from routes.setting import router as setting_router
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
app.include_router(router, prefix='/chat')
app.include_router(setting_router, prefix='/setting')

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
    result = crud.test(db=db, item=item)
    # result = crud.sendLine(db=db, item=item)
    return result
