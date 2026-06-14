import os
from datetime import timedelta
from dotenv import load_dotenv

#load environment variables from the .env file
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key-if-env-fails")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password@localhost:5432/leetcode_ai"
)