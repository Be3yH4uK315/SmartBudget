from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status

from app.api import dependencies
from app.core.exceptions import CategoryNotFoundError, ClassificationResultNotFoundError
from app.domain.schemas import api as schemas
from app.services.classification.service import ClassificationService

router = APIRouter(tags=["Classification"])


@router.get(
    "/classification/{transaction_id}",
    response_model=schemas.CategorizationResultResponse,
    summary="Получить результат классификации",
)
async def get_classification_result(
    transaction_id: UUID = Path(..., description="ID транзакции"),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: ClassificationService = Depends(dependencies.get_classification_service),
):
    """Возвращает результат классификации по ID транзакции."""
    try:
        return await service.get_classification(user_id, transaction_id)
    except ClassificationResultNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/feedback",
    response_model=schemas.UnifiedSuccessResponse,
    summary="Отправить feedback по классификации",
)
async def submit_feedback(
    body: schemas.FeedbackRequest = Body(...),
    user_id: UUID = Depends(dependencies.get_current_user_id),
    service: ClassificationService = Depends(dependencies.get_classification_service),
):
    """Принимает пользовательский feedback по результату классификации."""
    try:
        await service.submit_feedback(user_id, body)

        return schemas.UnifiedSuccessResponse(
            ok=True,
            detail="Feedback accepted",
        )

    except (ClassificationResultNotFoundError, CategoryNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
