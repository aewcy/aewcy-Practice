from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class User(Base):
    __tablename__ = "users" # 这会在 MySQL 里建一张叫 users 的表

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True,nullable=False)
    hashed_password = Column(String(255),nullable=False) 
    is_active = Column(Boolean, default=True,nullable=False)
    