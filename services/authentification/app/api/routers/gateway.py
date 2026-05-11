from fastapi import APIRouter, Depends, Request, Response, status

from app.api import dependencies
from app.services.session_service import SessionService
from app.services.token_service import TokenService

router = APIRouter(tags=["gateway"])


@router.get("/gateway-verify", include_in_schema=False)
async def gateway_verify(
    request: Request,
    token_service: TokenService = Depends(dependencies.get_token_service),
    session_service: SessionService = Depends(dependencies.get_session_service),
):
    """Легковесный endpoint для проверки пользователя через API Gateway."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        payload = await token_service.decode_token(access_token, verify_exp=True)

        user_id = payload.get("sub")
        session_id = payload.get("sid")

        if not user_id or not session_id:
            return Response(status_code=status.HTTP_401_UNAUTHORIZED)

        is_valid = await session_service.verify_session_fast(session_id)
        if not is_valid:
            return Response(status_code=status.HTTP_401_UNAUTHORIZED)

        return Response(
            status_code=status.HTTP_200_OK,
            headers={"X-User-Id": user_id},
        )

    except Exception:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)
