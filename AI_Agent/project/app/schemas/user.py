from pydantic import BaseModel


class UserBase(BaseModel):
    username: str


class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    password: str
