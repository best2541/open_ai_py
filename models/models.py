from sqlalchemy import Column, Integer, String, TIMESTAMP
from utilites.database import Base

class User(Base):
    __tablename__ = "USERS"

    user_id = Column(String(255), primary_key=True)
    username = Column(String(100))
    password = Column(String(100))
    age = Column(Integer)
    country = Column(Integer)

class Activities(Base):
    __tablename__ = "ACTIVITIES"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), nullable=False)
    topic = Column(String(100), nullable=False)
    start_date_time = Column(TIMESTAMP)

class Countries(Base):
    __tablename__ = "COUNTRY"

    id = Column(Integer, primary_key=True)
    country_name = Column(String(100), nullable=False)
class Logs(Base):
    __tablename__ = "Logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255))
    detail = Column(String(255))
    create_date = Column(TIMESTAMP)
