from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models
from database import engine, SessionLocal
import security
from pydantic import BaseModel

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

class LoginUser(BaseModel):
    username: str
    password: str

@app.post("/register")
def register(user: CreateUser, db: Session = Depends(get_db)):
    # 查数据库是否已有该用户名
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户已存在")

    hashed_password = security.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "用户注册成功", "username": user.username}


@app.post("/login")
def login(user: LoginUser, db: Session = Depends(get_db)):
    # 从数据库查用户
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="用户不存在")

    is_valid = security.verify_password(user.password, db_user.hashed_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail="密码错误")

    return {"message": "登录成功", "username": user.username}