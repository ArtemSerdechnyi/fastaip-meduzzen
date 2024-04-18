from logging import getLogger
from fastapi import HTTPException, Depends, APIRouter
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserSignUpRequestScheme
from app.db.postgres import get_async_session
from app.services.user import UserService

router = APIRouter()
logger = getLogger(__name__)


@router.post("/create")
async def create_new_user(
    user: UserSignUpRequestScheme,
    db: AsyncSession = Depends(get_async_session),
):
    try:
        await UserService(db).create_user(
            username=user.username,
            email=user.email,
            password=user.password,
        )
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(status_code=503, detail=f"Database error: {err}")

    return {"status_code": 200, "detail": "User created"}
