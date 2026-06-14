import os
from datetime import timedelta

# In a real production app, these would be loaded from your .env file
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Replace 'your_password' with your actual pgAdmin/PostgreSQL password
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:your_password@localhost:5432/leetcode_ai"
)