from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.api.deps import get_current_user
from src.service import submission_services

router = APIRouter(prefix="/submissions", tags=["Code Execution"])

# Input schema from the frontend
class CodeSubmission(BaseModel):
    question_id: int
    code: str

@router.post("/run")
def execute_code(
    submission: CodeSubmission, 
    current_user = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Pass the raw data straight to the logic layer
    result = submission_services.run_code_submission(
        db=db, 
        question_id=submission.question_id, 
        code=submission.code
    )
    
    # If the service returned None, it means the database query came up empty
    if result is None:
        raise HTTPException(status_code=404, detail="Question not found")
        
    return result