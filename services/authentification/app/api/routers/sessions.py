from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Request
from fastapi_limiter.depends import RateLimiter

from app.api import dependencies
from app.domain.schemas import api as schemas
from app.domain.schemas import dtos
from app.services.session_service import SessionService

router = APIRouter(tags=["sessions"])


@router.patch(
    "/sessions/retention",
    status_code=200,
    response_model=schemas.UnifiedResponse,
    summary="Обновление настроек хранения сессий пользователя",
)
async def update_retention_settings(
    body: schemas.UpdateRetentionRequest = Body(...),
    session_service: SessionService = Depends(dependencies.get_session_service),
    user: dtos.UserDTO = Depends(dependencies.get_current_active_user),
):
    await session_service.update_user_retention_settings(user.user_id, body.days)

    return schemas.UnifiedResponse(
        status="success",
        action="updateRetention",
        detail=f"Session retention updated to {body.days} days.",
    )


@router.get(
    "/sessions/retention",
    status_code=200,
    response_model=schemas.RetentionInfo,
    summary="Получение настроек хранения сессий пользователя",
)
async def get_retention_settings(
    user: dtos.UserDTO = Depends(dependencies.get_current_active_user),
):
    return schemas.RetentionInfo(days=user.retention_days)


@router.get(
    "/sessions",
    status_code=200,
    response_model=schemas.AllSessionsResponse,
    summary="Получение всех сессий пользователя",
)
async def get_all_user_sessions(
    request: Request,
    session_service: SessionService = Depends(dependencies.get_session_service),
    user: dtos.UserDTO = Depends(dependencies.get_current_active_user),
):
    current_refresh_token = request.cookies.get("refresh_token")

    sessions_list = await session_service.get_all_sessions(
        user.user_id,
        current_refresh_token,
    )

    return schemas.AllSessionsResponse(sessions=sessions_list)


@router.delete(
    "/sessions/{sessionId}",
    status_code=200,
    response_model=schemas.UnifiedResponse,
    summary="Ревокация сессии пользователя по ID",
)
async def revoke_session(
    session_id: UUID = Path(..., alias="sessionId"),
    session_service: SessionService = Depends(dependencies.get_session_service),
    user: dtos.UserDTO = Depends(dependencies.get_current_active_user),
):
    await session_service.revoke_session(user.user_id, session_id)

    return schemas.UnifiedResponse(
        status="success",
        action="revokeSession",
        detail="Session has been revoked.",
    )


@router.post(
    "/sessions/logout-others",
    status_code=200,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    response_model=schemas.UnifiedResponse,
    summary="Ревокация всех других сессий пользователя",
)
async def revoke_other_sessions(
    request: Request,
    session_service: SessionService = Depends(dependencies.get_session_service),
    user: dtos.UserDTO = Depends(dependencies.get_current_active_user),
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    await session_service.revoke_other_sessions(user.user_id, refresh_token)

    return schemas.UnifiedResponse(
        status="success",
        action="revokeOtherSessions",
        detail="All other sessions have been revoked.",
    )
