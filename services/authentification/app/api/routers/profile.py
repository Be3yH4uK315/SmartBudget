from fastapi import APIRouter, Body, Depends, Response
from fastapi_limiter.depends import RateLimiter

from app.api import dependencies
from app.domain.schemas import api as schemas
from app.domain.schemas import dtos
from app.services.profile_service import ProfileService
from app.utils import cookies

router = APIRouter(tags=["user"])


@router.get(
    "/me",
    status_code=200,
    response_model=schemas.UserInfo,
    summary="Получение информации о текущем пользователе",
)
async def get_current_user_info(
    user: dtos.UserDTO = Depends(dependencies.get_current_active_user),
):
    return user


@router.patch(
    "/me/profile",
    status_code=200,
    response_model=schemas.UnifiedResponse,
    summary="Обновление профиля пользователя",
)
async def update_profile(
    body: schemas.UpdateProfileRequest = Body(...),
    profile_service: ProfileService = Depends(dependencies.get_profile_service),
    user: dtos.UserDTO = Depends(dependencies.get_current_active_user),
):
    await profile_service.update_profile(user.user_id, body)

    return schemas.UnifiedResponse(
        status="success",
        action="updateProfile",
        detail="Profile updated successfully.",
    )


@router.patch(
    "/language",
    status_code=200,
    response_model=schemas.UnifiedResponse,
    summary="Обновление языка интерфейса пользователя",
)
async def update_language(
    body: schemas.UpdateLanguageRequest = Body(...),
    profile_service: ProfileService = Depends(dependencies.get_profile_service),
    user: dtos.UserDTO = Depends(dependencies.get_current_active_user),
):
    await profile_service.update_language(user.user_id, body)

    return schemas.UnifiedResponse(
        status="success",
        action="updateLanguage",
        detail="Language updated successfully.",
    )


@router.post(
    "/me/email/request",
    status_code=200,
    dependencies=[Depends(RateLimiter(times=3, seconds=60))],
    response_model=schemas.UnifiedResponse,
    summary="Инициация смены email пользователя",
)
async def request_email_change(
    body: schemas.InitiateEmailChangeRequest = Body(...),
    profile_service: ProfileService = Depends(dependencies.get_profile_service),
    user: dtos.UserDTO = Depends(dependencies.get_current_active_user),
):
    await profile_service.initiate_email_change(user.user_id, body)

    return schemas.UnifiedResponse(
        status="success",
        action="requestEmailChange",
        detail=f"Confirmation email sent to {body.new_email}.",
    )


@router.post(
    "/me/email/confirm",
    status_code=200,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse,
    summary="Подтверждение смены email пользователя",
)
async def confirm_email_change(
    response: Response,
    body: schemas.ConfirmEmailChangeRequest = Body(...),
    profile_service: ProfileService = Depends(dependencies.get_profile_service),
):
    await profile_service.confirm_email_change(body)
    cookies.delete_auth_cookies(response)

    return schemas.UnifiedResponse(
        status="success",
        action="confirmEmailChange",
        detail="Email successfully changed. Please log in with your new email.",
    )
