from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...core.deps import get_db
from ...schemas.auth import CreateUser, Token
from ...services.auth_service import register_user, login_user

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: CreateUser, db: Session = Depends(get_db)):
    result = register_user(db, user_data)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"],
            headers={"WWW-Authenticate": "Bearer"}
        )
    return {"message": result["message"], "username": result["username"]}


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    result = login_user(db, form_data.username, form_data.password)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["message"],
            headers={"WWW-Authenticate": "Bearer"}
        )
    return {"access_token": result["access_token"], "token_type": result["token_type"]}
