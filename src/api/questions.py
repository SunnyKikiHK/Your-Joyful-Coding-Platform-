from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.schemas import question as question_schemas
from src.crud import question as question_crud

router = APIRouter(prefix="/questions", tags=["Questions"])

@router.post("/", response_model=question_schemas.QuestionResponse, status_code=201)
def create_question(question: question_schemas.QuestionCreate, db: Session = Depends(get_db)):
    #in production, add an admin dependency here to allow admins to create questions
    return question_crud.create_question(db=db, question=question)

@router.get("/", response_model=List[question_schemas.QuestionResponse])
def read_questions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return question_crud.get_questions(db, skip=skip, limit=limit)

@router.get("/{question_id}", response_model=question_schemas.QuestionResponse)
def read_question(question_id: int, db: Session = Depends(get_db)):
    db_question = question_crud.get_question(db, question_id=question_id)
    if db_question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return db_question