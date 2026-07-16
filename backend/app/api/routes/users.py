from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Example protected route.
    Add Depends(get_current_user) to any route you want to protect.
    FastAPI reads the HttpOnly cookie automatically — no extra code needed.
    """
    return current_user


# When you build new features, copy this pattern:
#
#   @router.get("/my-data")
#   async def my_data(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
#       ...fetch user's data from db using user.id...
