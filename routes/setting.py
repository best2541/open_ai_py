from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from controllers import crud
from utilites.database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@router.get('/getallcountries')
def get_country(db: Session = Depends(get_db)):
    result = crud.get_countries(db=db)
    if result is None:
        return []
    else:
        return result