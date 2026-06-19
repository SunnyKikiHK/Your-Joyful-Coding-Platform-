import enum
from sqlalchemy import Column, Integer, String, Text, Enum, JSON
from src.db.database import Base

class DifficultyLevel(str, enum.Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True, nullable=False)
    difficulty = Column(Enum(DifficultyLevel), nullable=False)
    topics = Column(JSON, default=list)
    description = Column(Text, nullable=False)
    test_cases = Column(JSON, default=list)