from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus
import os

password = quote_plus(os.getenv("DB_PASSWORD", "wxnlyzds310!"))

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://root:{password}@db:3306/agent_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
