import os
from sqlalchemy.orm import Session
from models.models import User,Activities,Countries,Logs
from passlib.context import CryptContext
from pydantic import BaseModel
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.prompts.chat import ChatPromptTemplate
from langchain.agents.agent_types import AgentType
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, desc
from langchain.agents import create_sql_agent
from langdetect import detect,LangDetectException
from typing import Dict, Any
from openai import OpenAI
from fastapi import HTTPException
from datetime import datetime
import requests
import json
import random
import string

class MessageResponse(BaseModel):
    text: str
    sender: str

class Item(BaseModel):
    items: list[MessageResponse]
    q: str

class HumanMessage:
    def __init__(self, content: str):
        self.content = content
        
def detect_language(text):
    try:
        language = detect(text)
        return language
    except LangDetectException as e:
        # print(f"Error detecting language: {e}")
        return "unknown"
    
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

def check_user(db: Session, user_id: str):
    return db.query(User).filter(User.user_id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).offset(skip).limit(limit).all()

def insert_log(db: Session, user_id: str, detail: str):
    # return db.query(Logs).offset(0).limit(10).first()
    db_log = Logs(user_id=user_id, detail=detail, create_date=datetime.now())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_log(db: Session, user_id: str):
    # return db.query(Logs).offset(0).limit(10).all()
    return db.query(Logs).filter(Logs.user_id == user_id).order_by(desc(Logs.create_date)).first()

def create_user(db: Session, username: str, password: str, age: int, country: int):
    random_string = ''.join(random.choices(string.digits, k=10))
    db_user = User(user_id=random_string, username=username, password=get_password_hash(password), age=age, country=country)
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
    print('db', db)
    return db.query(Countries).all()

def get_audio_message(message_id: str) -> bytes:
    LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
    headers = {
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    response = requests.get(url, headers=headers, stream=True)
    if response.status_code == 200:
        return response.content
    else:
        print('failed')
        raise HTTPException(status_code=response.status_code, detail=response.text)

def save_audio_file(message_id: str, content: bytes):
    with open(f"./assets/audio/test.mp3", "wb") as f:
        f.write(content)

def line_send_text(text:str, to:str):
    LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
    LINE_USER_ID = to
        
    headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
        }
        
    data = {
        "to": LINE_USER_ID,
        "messages": [{
            "type": "text",
            "text": text
        }]
    }
        
    response = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        print("Failed to send message:", response.status_code, response.text)
    else:
        print("Message sent successfully!")
            
def sendLine(db: Session, item:Dict[str,Any]):
    # result = insert_log(db=db, user_id='user_id', detail="meeting")
    # print(result)
    # return 'test'
    
    result = ''
    for event in item['events']:
        user_id = event["source"]["userId"]
        check = check_user(db, user_id=user_id)
        if(check != None):
            json_object = ['','','','']
            try:
                log = get_log(db=db,user_id=user_id)
                json_object = json.loads(log.detail)
            except json.JSONDecodeError as error:
                json_object = ['','','','']
            print(json_object)
            if event["type"] == "message" and event["message"]["type"] == "audio":
                message_id = event["message"]["id"]
                try:
                    audio_content = get_audio_message(message_id)
                    save_audio_file(message_id, audio_content)
                    prepare = [
                        (
                            "system", """
                            You are a very intelligent AI assistant who is an expert in identifying relevant questions from the user and converting them into SQL queries to generate correct answers.
                            And if the user asks something related to the context below, please use the context below to write the SQL queries.
                            Context:
                            You must query against the connected database, which has a total of 3 tables: USERS and COUNTRY and ACTIVITIES.
                            The USERS table has columns username, age, country and user_id. It provides user information.
                            The COUNTRY table has columns id (foreign key with USERS table country column) and country_name. It provides country-specific information.
                        
                            As an expert, you don't have to create table, you must use joins, updates, and inserts whenever required.
                            make query performance fastest as you can.
                            tell user a result even you got nothing tell him is nothing.
                            """
                        ),
                        ['user',json_object[1]],
                        ['ai',json_object[3]]
                    ]
                    client = OpenAI(api_key=os.getenv('OPEN_API_KEY'))
                    audio_file= open("./assets/audio/test.mp3", "rb")
                    translation = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                    language='th'
                    )
        
                    lang = detect_language(translation.text)
                    if(lang == 'th'):
                        translation.text = translation.text +'ตอบเป็นภาษาไทย'
                    prepare.append(("user","{question}"))
        
                    cs=os.getenv('SOURCE')
                    # db_engine = create_engine(connectionString)
                    db_engine=create_engine(cs)
                    _db=SQLDatabase(db_engine)
                    llm=ChatOpenAI(streaming=True,temperature=0.0,model="gpt-4",openai_api_key=os.getenv('OPEN_API_KEY'))
                    sql_toolkit=SQLDatabaseToolkit(db=_db,llm=llm)
                    sql_toolkit.get_tools()
                    prompt=ChatPromptTemplate.from_messages(prepare)
                    agent=create_sql_agent(llm=llm,toolkit=sql_toolkit,agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,verbose=True,max_execution_time=30,max_iterations=10,handle_parsing_errors=True)
                    result = agent.invoke(prompt.format_prompt(question=translation.text))
                except Exception as e:
                    print('ERROR')
                    # raise HTTPException(status_code=500, detail=str(e))
            if event["type"] == "message" and event["message"]["type"] == "text":
                text = item['events'][0]['message']['text']
                print('log_test')
                print(json_object[3])
                prepare = [
                    (
                        "system", f"""
                        You are a very intelligent AI assistant who is an expert in identifying relevant questions from the user and converting them into SQL queries to generate correct answers.
                        And if the user asks something related to the context below, please use the context below to write the SQL queries.
                        Context:
                        My user_id is '{user_id}'
                        You must query against the connected database, which has a total of 3 tables: USERS and COUNTRY and ACTIVITIES.
                        The USERS table has columns username, age, country and user_id. It provides user information.
                        The COUNTRY table has columns id (foreign key with USERS table country column) and country_name. It provides country-specific information.
                        The ACTIVITIES table has columns id and user_id (foreign key with USERS table user_id column), topic and start_date_time(user will give date,time to you if user don't give you a date what say it today, if user don't give you the time you can ask for it). It provides activities to do each day.
                        As an expert, you don't have to create table, you must updates, and inserts whenever required avoid using joins as much as possible.
                        make query performance fastest as you can.
                        tell user a result even you got nothing tell him is nothing.
                        """
                    ),
                    ('user',json_object[1]),
                    ('ai',json_object[3])
                ]

                lang = detect_language(text)

                if(lang == 'th'):
                    text = text +'ตอบเป็นภาษาไทย'
                prepare.append(("user","{question}"))

                cs=os.getenv('SOURCE')
                db_engine=create_engine(cs)
                _db=SQLDatabase(db_engine)
                llm=ChatOpenAI(streaming=True,temperature=0.0,model="gpt-4",openai_api_key=os.getenv('OPEN_API_KEY'))
                sql_toolkit=SQLDatabaseToolkit(db=_db,llm=llm)
                sql_toolkit.get_tools()
                prompt=ChatPromptTemplate.from_messages(prepare)
                agent=create_sql_agent(llm=llm,toolkit=sql_toolkit,agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,verbose=True,max_execution_time=60,max_iterations=10,handle_parsing_errors=True)
                result = agent.invoke(prompt.format_prompt(question=text))
        
            line_send_text(text=result['output'], to=item['events'][0]['source']['userId'])
        else:
            if event["type"] == "message" and event["message"]["type"] == "text":
                id = item['events'][0]['source']['userId']
                text = item['events'][0]['message']['text']
        
                prepare = [
                    (
                        "system", f"""
                        You are a very intelligent AI assistant who is an expert in identifying relevant questions from the user and converting them into SQL queries to register new user.
                        And if the user give his personal data or even just only user_id use it to update to database if user_id is already exist else insert it.
                        Context:
                        My user_id is '{id}'
                        You must query against the connected database, which has a total of 3 tables: USERS and COUNTRY and ACTIVITIES.
                        The USERS table has columns username, age, country and user_id. It provides user information.
                        The COUNTRY table has columns id (foreign key with USERS table country column) and country_name. It provides country-specific information.
                    
                        As an expert, you don't have to create table, you must updates, and inserts whenever required avoid using joins as much as possible.
                        make query performance fastest as you can.
                        tell user a result even you got nothing tell him is nothing.
                        """
                    )
                ]

                lang = detect_language(text)
        
                if(lang == 'th'):
                    text = text +'ตอบเป็นภาษาไทย'
                prepare.append(("user","{question}"))
        
                cs=os.getenv('SOURCE')
                db_engine=create_engine(cs)
                _db=SQLDatabase(db_engine)
                llm=ChatOpenAI(streaming=True,temperature=0.0,model="gpt-4",openai_api_key=os.getenv('OPEN_API_KEY'))
                sql_toolkit=SQLDatabaseToolkit(db=_db,llm=llm)
                sql_toolkit.get_tools()
                prompt=ChatPromptTemplate.from_messages(prepare)
                agent=create_sql_agent(llm=llm,toolkit=sql_toolkit,agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,verbose=True,max_execution_time=60,max_iterations=10,handle_parsing_errors=True)
                result = agent.invoke(prompt.format_prompt(question=text))
                line_send_text(text=result['output'], to=item['events'][0]['source']['userId'])
        input = ''
        for test in result['input']:
            input = test[1][1]
        
    insert_log(db=db, user_id=user_id, detail=f'["user","{input.content}","ai","{result['output']}"]')
                    
    return 'item'

def read_text(items:Item = []):
    prepare = [
        (
        "system", """
        You are a very intelligent AI assistant who is an expert in identifying relevant questions from the user and converting them into SQL queries to generate correct answers.
        And if the user asks something related to the context below, please use the context below to write the SQL queries.
        Context:
        You must query against the connected database, which has a total of 3 tables: USERS and COUNTRY and ACTIVITIES.
        The USERS table has columns username, age, country and user_id. It provides user information.
        The COUNTRY table has columns id (foreign key with USERS table country column) and country_name. It provides country-specific information.
        The ACTIVITIES table has columns id and user_id (foreign key with USERS table user_id column), topic and start_date. It provides activities to do each day.
        As an expert, you don't have to create table, you must updates, and inserts whenever required avoid using joins as much as possible.
        make query performance fastest as you can.
        tell user a result even you got nothing tell him is nothing.
        """
        )
    ]
    for x in items.items:
        if x.sender != 'AI':
            prepare.append(('user',x.text))
        else:
            prepare.append(('ai',x.text))
    lang = detect_language(items.q)
	
    if(lang == 'th'):
        items.q = items.q +'ตอบเป็นภาษาไทย'
    prepare.append(("user","{question}"))
    
    cs=os.getenv('SOURCE')
    db_engine=create_engine(cs)
    db=SQLDatabase(db_engine)
    llm=ChatOpenAI(streaming=True,temperature=0.0,model="gpt-4",openai_api_key=os.getenv('OPEN_API_KEY'))
    sql_toolkit=SQLDatabaseToolkit(db=db,llm=llm)
    sql_toolkit.get_tools()
    prompt=ChatPromptTemplate.from_messages(prepare)
    agent=create_sql_agent(llm=llm,toolkit=sql_toolkit,agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,verbose=True,max_execution_time=30,max_iterations=10,handle_parsing_errors=True)
    result = agent.invoke(prompt.format_prompt(question=items.q))
    return (result)
