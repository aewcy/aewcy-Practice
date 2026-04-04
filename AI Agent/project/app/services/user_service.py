from sqlalchemy.orm import Session
from ..models.user import User
from ..schemas.user import UserResponse


def get_user_info(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        is_active=user.is_active
    )
