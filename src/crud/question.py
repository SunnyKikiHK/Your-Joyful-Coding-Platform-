from sqlalchemy.orm import Session
from src.db import models
from src.schemas import question as question_schemas

def get_question(db: Session, question_id: int):
    return db.query(models.Question).filter(models.Question.id == question_id).first()

def get_questions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Question).offset(skip).limit(limit).all()

def create_question(db: Session, question: question_schemas.QuestionCreate):
    # Convert Pydantic schemas to dictionaries for JSON storage
    test_cases_data = [tc.model_dump() for tc in question.test_cases]
    
    db_question = models.Question(
        title=question.title,
        difficulty=question.difficulty,
        topics=question.topics,
        description=question.description,
        test_cases=test_cases_data
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question