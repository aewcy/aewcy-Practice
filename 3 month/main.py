from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from pydantic import BaseModel


import models
import security
from fake_users_db import fake_users_db, add_user, user_exists

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

def User_credentials_exception():
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
    db_user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not db_user:
        User_credentials_exception()

    is_valid = security.verify_password(form_data.password, db_user.hashed_password)
    if not is_valid:
        User_credentials_exception()

    if not getattr(db_user, "is_active", True):
        User_credentials_exception()

    return {"access_token": security.create_access_token(data={"sub": db_user.username}), "token_type": "bearer"}



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(token:str = Depends(oauth2_scheme),db:Session = Depends(get_db)):
    get_credentials_exception = HTTPException(
        status_code = 401,
        detail = "错误凭证",
        headers = {"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise get_credentials_exception
        db_user = db.query(models.User).filter(models.User.username == username).first()
        if db_user is None:
            raise get_credentials_exception 
        return db_user
    except JWTError:
        raise get_credentials_exception 

def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    check_user_status_exception = HTTPException(
    status_code = 403,
    detail = "用户账户当前不可用"
    )
    if not current_user.is_active:
        raise check_user_status_exception
    return current_user


@app.get("/users/me")
def get_authenticated_user_info(current_user: models.User = Depends(get_current_active_user)):    
    current_user_dict = {"username": current_user.username,
    }
    return current_user_dict
