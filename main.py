from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routes.chat import router
from routes.users import router as users_router
from routes.setting import router as setting_router

# Create all tables
# from models import Base
# Base.metadata.create_all(bind=engine)

app = FastAPI()

load_dotenv()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include the router
app.include_router(users_router, prefix="/users")
app.include_router(router, prefix='/chat')
app.include_router(setting_router, prefix='/setting')

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)