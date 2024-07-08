import os
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents.agent_types import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.sql_database import SQLDatabase
from langchain.prompts.chat import ChatPromptTemplate
from sqlalchemy import create_engine
from openai import OpenAI

client = OpenAI(api_key='')
audio_file= open("./assets/audio/country.mp3", "rb")
translation = client.audio.translations.create(
  model="whisper-1", 
  file=audio_file
)
print(translation.text)
client = OpenAI(api_key='')
cs="mysql+pymysql://idewofktlttgg7nz:d1yjz40wualr5w69@dcrhg4kh56j13bnu.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/aoe1adeab51zt65c"
# db_engine = create_engine(connectionString)
db_engine=create_engine(cs)
db=SQLDatabase(db_engine)
llm=ChatOpenAI(temperature=0.0,model="gpt-4",openai_api_key='')
sql_toolkit=SQLDatabaseToolkit(db=db,llm=llm)
sql_toolkit.get_tools()
prompt=ChatPromptTemplate.from_messages([
    (
        "system",
        """
        you are a very intelligent AI assitasnt who is expert in identifying relevant questions from user and converting into sql queriesa to generate correcrt answer.
        Please use the below context to write the mysql queries.
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
agent.run(prompt.format_prompt(question=translation.text))