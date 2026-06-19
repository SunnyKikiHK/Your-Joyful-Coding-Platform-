import os
import shutil
from uuid import uuid4
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.schemas import user as user_schemas
from src.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["User Profile"])

#ensure the upload directory exists
UPLOAD_DIR = "static/avatars"
os.makedirs(UPLOAD_DIR, exist_ok=True)

#user changing pfp
@router.post("/me/avatar", response_model=user_schemas.UserResponse)
def upload_avatar(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    #validate that the file is actually an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    #generate a unique filename to prevent overwriting
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{current_user.id}_{uuid4().hex}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    #save the file to the local disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    #update the user's database record
    current_user.profile_picture_url = f"/{file_path}"
    db.commit()
    db.refresh(current_user)

    return current_user