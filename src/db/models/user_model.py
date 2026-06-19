from sqlalchemy import Column, Integer, String, Boolean
from src.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    #customisation
    profile_picture_url = Column(String, default="/static/avatars/default.png")
    
    #user stats
    is_active = Column(Boolean, default=True)
    problems_solved = Column(Integer, default=0)