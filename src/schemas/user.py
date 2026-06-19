from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    problems_solved: int
    profile_picture_url: str

    class Config:
        from_attributes = True

#token schema for login
class Token(BaseModel):
    access_token: str
    token_type: str