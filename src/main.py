import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.db.database import engine
from src.db import models
from src.api import auth, users

models.Base.metadata.create_all(bind=engine)

os.makedirs("static/avatars", exist_ok=True)

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

# SERVE STATIC FILES: Allows frontend to access images via http://127.0.0.1:8000/static/avatars/...
app.mount("/static", StaticFiles(directory="static"), name="static")

#attach the routers APIs
app.include_router(auth.router)
app.include_router(users.router)

@app.get("/")
def health_check():
    return {"status": "healthy", "message": "Welcome to your joyful coding platform AI API (we love viber!)"}