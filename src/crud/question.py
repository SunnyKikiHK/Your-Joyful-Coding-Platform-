from sqlalchemy.orm import Session
from sqlalchemy import cast, String, or_
from typing import Optional, List
from src.db import models
from src.schemas import question as question_schemas

def get_question(db: Session, question_id: int):
    return db.query(models.Question).filter(models.Question.id == question_id).first()

#server-side filtering logic
def get_questions(
    db: Session, 
    skip: int = 0, 
    limit: int = 50,
    search: Optional[str] = None,
    difficulty: Optional[str] = None,
    topics: Optional[List[str]] = None
):
    query = db.query(models.Question)

    #apply search filter (matches title or topics)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Question.title.ilike(search_term),
                # Cast JSON to string to search inside the array easily
                cast(models.Question.topics, String).ilike(search_term) 
            )
        )

    #apply difficulty filter
    if difficulty and difficulty != "All":
        query = query.filter(models.Question.difficulty == difficulty)

    #apply topic filters (Question must contain all selected topics)
    if topics:
        for topic in topics:
            query = query.filter(cast(models.Question.topics, String).ilike(f"%\"{topic}\"%"))

    total_count = query.count()
    
    items = query.offset(skip).limit(limit).all()

    return total_count, items

def create_question(db: Session, question: question_schemas.QuestionCreate):
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