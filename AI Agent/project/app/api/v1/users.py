from fastapi import APIRouter, Depends

from ...core.deps import get_current_active_user
from ...models.user import User
from ...schemas.user import UserResponse
from ...services.user_service import get_user_info

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return get_user_info(current_user)
