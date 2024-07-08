from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

@app.post("/")
async def uploadfile(files: list[UploadFile]):
	try: 
		for file in files:
			file_path = f"{file.filename}"
			with open(file_path, "wb") as f:
				f.write(file.file.read())
				return {"message": "File saved successfully"}
	except Exception as e:
		return {"message": e.args}
