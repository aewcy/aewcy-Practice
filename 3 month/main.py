from fastapi import FastAPI, Depends, HTTPException,status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from pydantic import BaseModel

import models
import security

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    """请求结束时自动关闭 session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CreateUser(BaseModel):
    username: str
    password: str

def credentials_exception():
    credentials_exception = HTTPException(
        status_code = 401,
        detail = "密码/用户名错误",
        headers = {"WWW-Authenticate": "Bearer"},
    )
    raise credentials_exception

@app.post("/register")
def register(user: CreateUser, db: Session = Depends(get_db)):
    # 查数据库是否已有该用户名
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        credentials_exception = HTTPException(
            status_code = 400,
            detail = "用户已存在",
            headers = {"WWW-Authenticate": "Bearer"},
        )
        raise credentials_exception

    hashed_password = security.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "用户注册成功", "username": user.username}




@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 从数据库查用户
    db_user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not db_user:
        credentials_exception()

    is_valid = security.verify_password(form_data.password, db_user.hashed_password)
    if not is_valid:
        credentials_exception()

    if not getattr(db_user,"is_active",True):
        credentials_exception()

    return {"access_token": security.create_access_token(data={"sub": db_user.username}), "token_type": "bearer"}