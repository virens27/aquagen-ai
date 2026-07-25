from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import ask, health

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(ask.router)


@app.get("/")
def root():
    return {"status": "AquaGen AI is running"}
