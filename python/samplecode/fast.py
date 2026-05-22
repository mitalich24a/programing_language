from fastapi import FastAPI
import uvicorn

app = FastAPI()


@app.get("/")
def get_home():
	print("Home Page")
	return {"message": "Home Page"}

@app.get("/home")
def get_home():
	print("Home Page")
	return {"message": "Home Page"}

uvicorn.run(app, host="127.0.0.1", port=8000)
