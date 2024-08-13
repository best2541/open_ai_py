import json
import os
from typing import Union
from fastapi import APIRouter, File, UploadFile, Form, Header
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from langchain.agents import create_sql_agent
# from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain.agents.agent_types import AgentType
# from langchain_community.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.prompts.chat import ChatPromptTemplate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from openai import OpenAI
from langdetect import detect,LangDetectException
import jwt

DATABASE_URL = os.getenv('SOURCE')
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
router = APIRouter()

class MessageResponse(BaseModel):
    text: str
    sender: str

class Item(BaseModel):
    items: list[MessageResponse]
    q: str
    
ACCESS_TOKEN_EXPIRE_MINUTE = 800
    
def upload(files: list[UploadFile]):
	try: 
		for file in files:
			file_path = f"./assets/audio/{file.filename}"
			with open(file_path, "wb") as f:
				f.write(file.file.read())
				return {"message": "File saved successfully"}
	except Exception as e:
		return {"message": e.args}

def detect_language(text):
    try:
        language = detect(text)
        return language
    except LangDetectException as e:
        # print(f"Error detecting language: {e}")
        return "unknown"
    
@router.post("/")
async def uploadfile(files: list[UploadFile],items:str = Form(...)):
    items = json.loads(items)
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
        As an expert, you don't have to create table, you must use updates, and inserts whenever required avoid using joins as much as possible.
        make query performance fastest as you can.
        tell user a result even you got nothing tell him is nothing.
        """
        )
    ]
    
    for x in items:
        if x['sender'] != 'AI':
            prepare.append(('user',x['text']))
        else:
            prepare.append(('ai',x['text']))
    
    upload(files=files)
    
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
    db=SQLDatabase(db_engine)
    llm=ChatOpenAI(streaming=True,temperature=0.0,model="gpt-4",openai_api_key=os.getenv('OPEN_API_KEY'))
    sql_toolkit=SQLDatabaseToolkit(db=db,llm=llm)
    sql_toolkit.get_tools()
    prompt=ChatPromptTemplate.from_messages(prepare)
    agent=create_sql_agent(llm=llm,toolkit=sql_toolkit,agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,verbose=True,max_execution_time=30,max_iterations=10,handle_parsing_errors=True)
    result = agent.invoke(prompt.format_prompt(question=translation.text))
    return (result)

@router.post("/text/")
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
        As an expert, you don't have to create table, you must use updates, and inserts whenever required avoid using joins as much as possible.
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
    
@router.get("/id/{id}")
def read_id(id:int,q:Union[str,None] = None):
    return {"id":id,"q":q}

@router.post("/auth")
async def auth(Authorization: str | None = Header(default=None),items:Item = []):
    decode_jwt = jwt.decode(Authorization, os.getenv('SECRET_KEY'), algorithms=["HS256"])
    
    prepare = [
        (
        "system", f"""
        You are a very intelligent AI assistant who is an expert in identifying relevant questions from the user and converting them into SQL queries to generate correct answers.
        And if the user asks something related to the context below, please use the context below to write the SQL queries.
        Context:
        I am {decode_jwt['username']}
        You must query against the connected database, which has a total of 3 tables: USERS and COUNTRY and ACTIVITIES.
        The USERS table has columns username, age, country and user_id. It provides user information.
        The COUNTRY table has columns id (foreign key with USERS table country column) and country_name. It provides country-specific information.
        The ACTIVITIES table has columns id and user_id (foreign key with USERS table user_id column), topic and start_date. It provides activities to do each day.
        As an expert, you don't have to create table, you must use updates, and inserts whenever required avoid using joins as much as possible and you can not show user's data from anyone except my data.
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

@router.post("/auth/voice")
async def authUploadfile(files: list[UploadFile],items:str = Form(...),Authorization: str | None = Header(default=None)):
    items = json.loads(items)
    decode_jwt = jwt.decode(Authorization, os.getenv('SECRET_KEY'), algorithms=["HS256"])
    prepare = [
        (
        "system", f"""
        You are a very intelligent AI assistant who is an expert in identifying relevant questions from the user and converting them into SQL queries to generate correct answers.
        And if the user asks something related to the context below, please use the context below to write the SQL queries.
        Context:
        I am {decode_jwt['username']}
        You must query against the connected database, which has a total of 3 tables: USERS and COUNTRY and ACTIVITIES.
        The USERS table has columns username, age, country and user_id. It provides user information.
        The COUNTRY table has columns id (foreign key with USERS table country column) and country_name. It provides country-specific information.
        The ACTIVITIES table has columns id and user_id (foreign key with USERS table user_id column), topic and start_date. It provides activities to do each day.
        As an expert, you don't have to create table, you must use updates, and inserts whenever required avoid using joins as much as possible and you can not show user's data from anyone except his data.
        make query performance fastest as you can.
        tell user a result even you got nothing tell him is nothing.
        """
        )
    ]
    
    for x in items:
        if x['sender'] != 'AI':
            prepare.append(('user',x['text']))
        else:
            prepare.append(('ai',x['text']))
    
    upload(files=files)
    
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
    db=SQLDatabase(db_engine)
    llm=ChatOpenAI(streaming=True,temperature=0.0,model="gpt-4",openai_api_key=os.getenv('OPEN_API_KEY'))
    sql_toolkit=SQLDatabaseToolkit(db=db,llm=llm)
    sql_toolkit.get_tools()
    prompt=ChatPromptTemplate.from_messages(prepare)
    agent=create_sql_agent(llm=llm,toolkit=sql_toolkit,agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,verbose=True,max_execution_time=30,max_iterations=10,handle_parsing_errors=True)
    result = agent.invoke(prompt.format_prompt(question=translation.text))
    return (result)
