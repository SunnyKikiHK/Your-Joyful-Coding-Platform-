from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="YOUR JOYFUL CODING PLATFORM",
    description="Backend",
    version="0.1.0"
)

origins = [
    "http://localhost:3000",  # Common for React/Next.js
    "http://localhost:5173",  # Common for Vite
    "http://127.0.0.1:8000"
    #more later
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {
        "status": "healthy", 
        "message": "Welcome to the YOUR JOYFUL CODING PLATFORM API"
    }
