from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")


class ResponseBase(BaseModel):
    code: int = 200
    message: str = "Success"


class ResponseModel(ResponseBase, Generic[T]):
    data: T | None = None
