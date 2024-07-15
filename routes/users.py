from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from utilites.database import SessionLocal
from pydantic import BaseModel
import controllers.crud as crud
import os
import jwt

router = APIRouter()

SECRET_KEY = os.getenv('SECRET_KEY')
# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserBase(BaseModel):
    username: str
    password: str
    age: int
    country: int

@router.post("/newuser")
def create_user(user:UserBase, db: Session = Depends(get_db)):
    db_user = crud.create_user(db, username=user.username, password=user.password, age=user.age, country=user.country)
    return db_user

@router.get("/{username}")
def read_user(username: str, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/")
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.put("/{username}")
def update_user(username: str, age: int, country: int, db: Session = Depends(get_db)):
    db_user = crud.update_user(db, username=username, age=age, country=country)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.delete("/{username}")
def delete_user(username: str, db: Session = Depends(get_db)):
    db_user = crud.delete_user(db, username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

class LoginClass(BaseModel):
    username:str
    password:str

@router.post("/login")
async def login(login_item:LoginClass,db: Session = Depends(get_db)):
    data=jsonable_encoder(login_item)
    result = crud.auth(db=db,username=data['username'],password=data['password'])
    if result :
        encode_jwt = jwt.encode(data,os.getenv('SECRET_KEY'),algorithm="HS256")
        return {"token":encode_jwt}
    else:
        return HTTPException(status_code=402, detail="username or password is invalid")