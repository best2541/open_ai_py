import json
import os
from typing import Union
from fastapi import APIRouter, File, UploadFile, Form, Header
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents.agent_types import AgentType
from langchain_community.chat_models import ChatOpenAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.prompts.chat import ChatPromptTemplate
from sqlalchemy import create_engine
from openai import OpenAI
from langdetect import detect,LangDetectException
import jwt

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
        The USERS table has columns username, age, and country. It provides user information.
        The COUNTRY table has columns id (foreign key with USERS table country column) and country_name. It provides country-specific information.
        The ACTIVITIES table has columns id and username (foreign key with USERS table username column) and name and detail and due_date. It provides activities to do each day.  
        As an expert, you must use joins, updates, and inserts whenever required.
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
    
    cs="mysql+pymysql://idewofktlttgg7nz:d1yjz40wualr5w69@dcrhg4kh56j13bnu.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/aoe1adeab51zt65c"
    # db_engine = create_engine(connectionString)
    db_engine=create_engine(cs)
    db=SQLDatabase(db_engine)
    llm=ChatOpenAI(temperature=0.0,model="gpt-4",openai_api_key=os.getenv('OPEN_API_KEY'))
    sql_toolkit=SQLDatabaseToolkit(db=db,llm=llm)
    sql_toolkit.get_tools()
    prompt=ChatPromptTemplate.from_messages(prepare)
    agent=create_sql_agent(llm=llm,toolkit=sql_toolkit,agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,verbose=True,max_execution_time=100,max_iterations=1000)
    result = agent.run(prompt.format_prompt(question=translation.text))
    return (result)

@router.post("/text/")
def read_text(items:Item = [], q: str = None):
    prepare = [
        (
        "system", """
        You are a very intelligent AI assistant who is an expert in identifying relevant questions from the user and converting them into SQL queries to generate correct answers.
        And if the user asks something related to the context below, please use the context below to write the SQL queries.
        Context:
        You must query against the connected database, which has a total of 3 tables: USERS and COUNTRY and ACTIVITIES.
        The USERS table has columns username, age, and country. It provides user information.
        The COUNTRY table has columns id (foreign key with USERS table country column) and country_name. It provides country-specific information.
        The ACTIVITIES table has columns id and username (foreign key with USERS table username column) and name and detail and due_date. It provides activities to do each day.  
        As an expert, you must use joins, updates, and inserts whenever required.
        """
        )
    ]
    for x in items.items:
        if x.sender != 'AI':
            prepare.append(('user',x.text))
        else:
            prepare.append(('ai',x.text))
    lang = detect_language(q)
	
    if(lang == 'th'):
        items.q = items.q +'ตอบเป็นภาษาไทย'
    prepare.append(("user","{question}"))
    
    cs="mysql+pymysql://idewofktlttgg7nz:d1yjz40wualr5w69@dcrhg4kh56j13bnu.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/aoe1adeab51zt65c"
    db_engine=create_engine(cs)
    db=SQLDatabase(db_engine)
    llm=ChatOpenAI(temperature=0.0,model="gpt-4",openai_api_key=os.getenv('OPEN_API_KEY'))
    sql_toolkit=SQLDatabaseToolkit(db=db,llm=llm)
    sql_toolkit.get_tools()
    prompt=ChatPromptTemplate.from_messages(prepare)
    agent=create_sql_agent(llm=llm,toolkit=sql_toolkit,agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,verbose=True,max_execution_time=100,max_iterations=1000)
    result = agent.run(prompt.format_prompt(question=q))
    return (result)
    
@router.get("/id/{id}")
def read_id(id:int,q:Union[str,None] = None):
    return {"id":id,"q":q}

@router.post("/auth")
async def auth(Authorization: str | None = Header(default=None),items:Item = [], q: str = None):
    decode_jwt = jwt.decode(Authorization, os.getenv('SECRET_KEY'), algorithms=["HS256"])
    # return {"decode":decode_jwt['username'],"token":Authorization}
    
    prepare = [
        (
        "system", f"""
        You are a very intelligent AI assistant who is an expert in identifying relevant questions from the user and converting them into SQL queries to generate correct answers.
        And if the user asks something related to the context below, please use the context below to write the SQL queries.
        Context:
        this question is from user {decode_jwt['username']}
        You must query against the connected database, which has a total of 3 tables: USERS and COUNTRY and ACTIVITIES.
        The USERS table has columns username, age, and country. It provides user information.
        The COUNTRY table has columns id (foreign key with USERS table country column) and country_name. It provides country-specific information.
        The ACTIVITIES table has columns id and username (foreign key with USERS table username column) and name and detail and due_date. It provides activities to do each day.  
        As an expert, you must use joins, updates, and inserts whenever required and you can not show user's data from anyone except his data
        """
        )
    ]
    for x in items.items:
        if x.sender != 'AI':
            prepare.append(('user',x.text))
        else:
            prepare.append(('ai',x.text))
    lang = detect_language(q)
	
    if(lang == 'th'):
        items.q = items.q +'ตอบเป็นภาษาไทย'
    prepare.append(("user","{question}"))
    
    cs="mysql+pymysql://idewofktlttgg7nz:d1yjz40wualr5w69@dcrhg4kh56j13bnu.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/aoe1adeab51zt65c"
    db_engine=create_engine(cs)
    db=SQLDatabase(db_engine)
    llm=ChatOpenAI(temperature=0.0,model="gpt-4",openai_api_key=os.getenv('OPEN_API_KEY'))
    sql_toolkit=SQLDatabaseToolkit(db=db,llm=llm)
    sql_toolkit.get_tools()
    prompt=ChatPromptTemplate.from_messages(prepare)
    agent=create_sql_agent(llm=llm,toolkit=sql_toolkit,agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,verbose=True,max_execution_time=100,max_iterations=1000)
    result = agent.run(prompt.format_prompt(question=q))
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
        this question is from user {decode_jwt['username']}
        You must query against the connected database, which has a total of 3 tables: USERS and COUNTRY and ACTIVITIES.
        The USERS table has columns username, age, and country. It provides user information.
        The COUNTRY table has columns id (foreign key with USERS table country column) and country_name. It provides country-specific information.
        The ACTIVITIES table has columns id and username (foreign key with USERS table username column) and name and detail and due_date. It provides activities to do each day.  
        As an expert, you must use joins, updates, and inserts whenever required and you can not show user's data from anyone except his data
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
    
    cs="mysql+pymysql://idewofktlttgg7nz:d1yjz40wualr5w69@dcrhg4kh56j13bnu.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/aoe1adeab51zt65c"
    # db_engine = create_engine(connectionString)
    db_engine=create_engine(cs)
    db=SQLDatabase(db_engine)
    llm=ChatOpenAI(temperature=0.0,model="gpt-4",openai_api_key=os.getenv('OPEN_API_KEY'))
    sql_toolkit=SQLDatabaseToolkit(db=db,llm=llm)
    sql_toolkit.get_tools()
    prompt=ChatPromptTemplate.from_messages(prepare)
    agent=create_sql_agent(llm=llm,toolkit=sql_toolkit,agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,verbose=True,max_execution_time=100,max_iterations=1000)
    result = agent.run(prompt.format_prompt(question=translation.text))
    return (result)