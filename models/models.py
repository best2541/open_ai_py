from sqlalchemy import Column, Integer, String
from utilites.database import Base

class User(Base):
    __tablename__ = "USERS"

    username = Column(String(100), primary_key=True)
    password = Column(String(100))
    age = Column(Integer)
    country = Column(Integer)

class Activities(Base):
    __tablename__ = "ACTIVITIES"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    detail = Column(String(255))

class Countries(Base):
    __tablename__ = "COUNTRY"

    id = Column(Integer, primary_key=True)
    country_name = Column(String(100), nullable=False)