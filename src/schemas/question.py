from pydantic import BaseModel
from typing import List
from src.db.models import DifficultyLevel

#strongly typed schema for what a single testcase looks like
class TestCaseSchema(BaseModel):
    input: str
    expected_output: str

#base schema with all the shared fields
class QuestionBase(BaseModel):
    title: str
    difficulty: DifficultyLevel
    topics: List[str]
    description: str
    test_cases: List[TestCaseSchema]

#used when an admin/user creates a new question
class QuestionCreate(QuestionBase):
    pass

#when sending a question back to the React frontend
class QuestionResponse(QuestionBase):
    id: int

    class Config:
        from_attributes = True

#wrapper schema for server-side pagination
class PaginatedQuestionResponse(BaseModel):
    total: int
    items: List[QuestionResponse]