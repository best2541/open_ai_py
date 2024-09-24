from pydantic import BaseModel

class Token(BaseModel):
    token: str

class User(BaseModel):
    user: str

class CalendarEvent(BaseModel):
    user: str
    datas: object