from fastapi import FastAPI

from .core.database import engine, Base
from .api.router import api_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agent API", version="1.0.0")

app.include_router(api_router, prefix="/api/v1") 


@app.get("/")
def root():
    return {"message": "Agent API is running"}
