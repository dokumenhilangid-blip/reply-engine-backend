from fastapi import FastAPI
from database import init_db

app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {"status": "backend alive"}

@app.get("/test-db")
def test_db():
    return {"status": "database ready"}
