from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import shutil
import os
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents.agent_types import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.sql_database import SQLDatabase
from langchain.prompts.chat import ChatPromptTemplate
from sqlalchemy import create_engine
from openai import OpenAI
from langdetect import detect

app = FastAPI()

load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

def upload(files: list[UploadFile]):
	try: 
		for file in files:
			file_path = f"./assets/audio/{file.filename}"
			with open(file_path, "wb") as f:
				f.write(file.file.read())
				return {"message": "File saved successfully"}
	except Exception as e:
		return {"message": e.args}

@app.post("/")
async def uploadfile(files: list[UploadFile]):
    upload(files=files)
    client = OpenAI(api_key='')
    audio_file= open("./assets/audio/test.mp3", "rb")
    translation = client.audio.translations.create(
    model="whisper-1", 
    file=audio_file
    )
    print(translation.text)
    cs="mysql+pymysql://idewofktlttgg7nz:d1yjz40wualr5w69@dcrhg4kh56j13bnu.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/aoe1adeab51zt65c"
    # db_engine = create_engine(connectionString)
    db_engine=create_engine(cs)
    db=SQLDatabase(db_engine)
    llm=ChatOpenAI(temperature=0.0,model="gpt-4",openai_api_key=os.getenv('OPEN_API_KEY'))
    sql_toolkit=SQLDatabaseToolkit(db=db,llm=llm)
    sql_toolkit.get_tools()
    prompt=ChatPromptTemplate.from_messages([
        (
            "system",
            """
            you are a very intelligent AI assitasnt who is expert in identifying relevant questions from user and converting into sql queriesa to generate correcrt answer.
            Answer same language as user.
            And if user ask something relate with context below Please use the below context to write the mysql queries.
            context:
            you must query against the connected database, it has total 2 tables , these are users,country
            USERS table has username,age,country columns.It gives the user information.
            COUNTRY table has Id,country_name columns.It gives the country specific information.
            As an expert you must use joins whenever required.
            """
        ),
        ("user","{question}\ ai: ")
    ])
    agent=create_sql_agent(llm=llm,toolkit=sql_toolkit,agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,verbose=True,max_execution_time=100,max_iterations=1000)
    result = agent.run(prompt.format_prompt(question=translation.text))
    return (result)

@app.get("/text/")
def read_text(q: str = None):
    print('q = ', q)
    lang = detect(q)
	
    if(lang == 'th'):
        q = q +'ตอบเป็นภาษาไทย'
	
    print(q)
    cs="mysql+pymysql://idewofktlttgg7nz:d1yjz40wualr5w69@dcrhg4kh56j13bnu.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/aoe1adeab51zt65c"
    db_engine=create_engine(cs)
    db=SQLDatabase(db_engine)
    llm=ChatOpenAI(temperature=0.0,model="gpt-4",openai_api_key=os.getenv('OPEN_API_KEY'))
    sql_toolkit=SQLDatabaseToolkit(db=db,llm=llm)
    sql_toolkit.get_tools()
    prompt=ChatPromptTemplate.from_messages([
        (
        "system", """
        You are a very intelligent AI assistant who is an expert in identifying relevant questions from the user and converting them into SQL queries to generate correct answers.
        And if the user asks something related to the context below, please use the context below to write the SQL queries.
        Context:
        You must query against the connected database, which has a total of 2 tables: users and country.
        The USERS table has columns username, age, and country. It provides user information.
        The COUNTRY table has columns Id and country_name. It provides country-specific information.
        As an expert, you must use joins, updates, and inserts whenever required.
        """
        ),
        ("user","มี user ชื่อ pawat ไหม แล้วเขาอยู่ประเทศอะไร\ ai: ใช่ค่ะ มีผู้ใช้ที่ชื่อว่า pawat และเขาอาศัยอยู่ในประเทศ Canada"),
        ("user","{question}\ ai: ")
    ])
    agent=create_sql_agent(llm=llm,toolkit=sql_toolkit,agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,verbose=True,max_execution_time=100,max_iterations=1000)
    result = agent.run(prompt.format_prompt(question=q))
    return (result)
    
@app.get("/voice/{item_id}")
def read_item(item_id: int, q: str = None):
    client = OpenAI(api_key='')
    audio_file= open("./assets/audio/country.mp3", "rb")
    translation = client.audio.translations.create(
    model="whisper-1", 
    file=audio_file
    )
    print(translation.text)
	
    lang = detect(translation.text)
	
    if(lang == 'th'):
        translation.text = translation.text +'ตอบเป็นภาษาไทย'

    cs="mysql+pymysql://idewofktlttgg7nz:d1yjz40wualr5w69@dcrhg4kh56j13bnu.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/aoe1adeab51zt65c"
    # db_engine = create_engine(connectionString)
    db_engine=create_engine(cs)
    db=SQLDatabase(db_engine)
    llm=ChatOpenAI(temperature=0.0,model="gpt-4",openai_api_key=os.getenv('OPEN_API_KEY'))
    sql_toolkit=SQLDatabaseToolkit(db=db,llm=llm)
    sql_toolkit.get_tools()
    prompt=ChatPromptTemplate.from_messages([
        (
            "system",
            """
            you are a very intelligent AI assitasnt who is expert in identifying relevant questions from user and converting into sql queriesa to generate correcrt answer.
            Answer same language as user.
            And if user ask something relate with context below Please use the below context to write the mysql queries.
            context:
            you must query against the connected database, it has total 2 tables , these are users,country
            USERS table has username,age,country columns.It gives the user information.
            COUNTRY table has Id,country_name columns.It gives the country specific information.
            As an expert you must use joins whenever required.
            """
        ),
        ("user","{question}\ ai: ")
    ])
    agent=create_sql_agent(llm=llm,toolkit=sql_toolkit,agent_type=AgentType.OPENAI_FUNCTIONS,verbose=True,max_execution_time=100,max_iterations=1000)
    agent.run(prompt.format_prompt(question=translation.text))
    return {"item_id": item_id, "q": q}
