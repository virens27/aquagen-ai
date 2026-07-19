from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from query_engine import ask_aquagen
from app.routes import health

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)

class Question(BaseModel):
    question: str

@app.get("/")
def root():
    return {"status": "AquaGen AI is running"}

@app.post("/ask")
def ask(q: Question):
    result = ask_aquagen(q.question)
    return result