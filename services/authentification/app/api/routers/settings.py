from fastapi import APIRouter, Body, Depends

from app.api import dependencies
from app.domain.schemas import api as schemas
from app.domain.schemas import dtos
from app.services.password_service import PasswordService

router = APIRouter(tags=["auth settings"])


@router.post(
    "/change-password",
    status_code=200,
    response_model=schemas.UnifiedResponse,
    summary="Смена пароля пользователя",
)
async def change_password(
    body: schemas.ChangePasswordRequest = Body(...),
    pwd_service: PasswordService = Depends(dependencies.get_password_service),
    user: dtos.UserDTO = Depends(dependencies.get_current_active_user),
):
    await pwd_service.change_password(user.user_id, body)

    return schemas.UnifiedResponse(
        status="success",
        action="changePassword",
        detail="Password changed.",
    )
