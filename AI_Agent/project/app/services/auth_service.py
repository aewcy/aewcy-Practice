from datetime import timedelta
from sqlalchemy.orm import Session
from ..schemas.auth import CreateUser
from ..schemas.user import UserResponse
from ..crud.user import get_user_by_username, create_user, authenticate_user
from ..core.security import create_access_token
from ..core.config import ACCESS_TOKEN_EXPIRE_MINUTES


def register_user(db: Session, user_data: CreateUser) -> dict:
    existing_user = get_user_by_username(db, user_data.username)
    if existing_user:
        return {"success": False, "message": "用户已存在"}

    create_user(db, user_data)
    return {"success": True, "message": "用户注册成功", "username": user_data.username}


def login_user(db: Session, username: str, password: str) -> dict:
    user = authenticate_user(db, username, password)
    if not user:
        return {"success": False, "message": "密码/用户名错误"}

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer"
    }
