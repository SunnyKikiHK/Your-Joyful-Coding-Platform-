from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

#import database engine and models
from src.db.database import engine
from src.db import models
from src.api import auth

#create sql tables in if they don't exist yet
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LeetCode AI Clone API",
    description="Backend for AI-powered code evaluation platform",
    version="0.1.0"
)

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

@app.get("/")
def health_check():
    return {"status": "healthy", "message": "Welcome to the LeetCode AI API"}

#uvicorn src.main:app --reload