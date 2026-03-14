from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus

# 在这里填入你的新密码（不需要手动转义，直接放原密码）
password = quote_plus("wxnlyzds310!")

# 使用 f-string 动态拼接转义后的密码
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://root:{password}@db:3306/agent_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()