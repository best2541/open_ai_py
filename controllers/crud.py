from sqlalchemy.orm import Session
from models.models import User,Activities,Countries
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def auth(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    return verify_password(plain_password=password,hashed_password=user.password)
    
def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, username: str, password: str, age: int, country: int):
    db_user = User(username=username, password=get_password_hash(password), age=age, country=country)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, username: str, age: int, country: int):
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        db_user.age = age
        db_user.country = country
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, username: str):
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

def create_activitie(db: Session, username: str, name: str, detail: str):
    db_activities = Activities(username=username, name=name, detail=detail)
    db.add(db_activities)
    db.commit()
    db.refresh(db_activities)
    return db_activities

def get_countries(db: Session):
    return db.query(Countries).all()