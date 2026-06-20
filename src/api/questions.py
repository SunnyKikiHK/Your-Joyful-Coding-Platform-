from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.schemas import question as question_schemas
from src.crud import question as question_crud

router = APIRouter(prefix="/questions", tags=["Questions"])

@router.post("/", response_model=question_schemas.QuestionResponse, status_code=201)
def create_question(question: question_schemas.QuestionCreate, db: Session = Depends(get_db)):
    return question_crud.create_question(db=db, question=question)

#exposes query parameters for the React frontend
@router.get("/", response_model=question_schemas.PaginatedQuestionResponse)
def read_questions(
    skip: int = 0, 
    limit: int = 50, 
    search: Optional[str] = None,
    difficulty: Optional[str] = None,
    topics: List[str] = Query(default=[]),
    db: Session = Depends(get_db)
):
    total, items = question_crud.get_questions(
        db, skip=skip, limit=limit, search=search, difficulty=difficulty, topics=topics
    )
    return {"total": total, "items": items}

@router.get("/{question_id}", response_model=question_schemas.QuestionResponse)
def read_question(question_id: int, db: Session = Depends(get_db)):
    db_question = question_crud.get_question(db, question_id=question_id)
    if db_question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return db_question