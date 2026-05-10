import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from redis.asyncio import Redis

from app.core.config import settings
from app.core.exceptions import (
    CategoryNotFoundError,
    ClassificationResultNotFoundError,
)
from app.domain.schemas import api as api_schemas
from app.domain.schemas.kafka import TransactionNeedCategoryEvent
from smartbudget_shared.events import (
    ClassificationCompletedPayload,
    ClassificationUpdatedPayload,
    EventEnvelope,
    EventSource,
    NotificationPayload,
)
from app.infrastructure.db.models import (
    Category,
    ClassificationResult,
    ClassificationSource,
    Feedback,
)
from app.infrastructure.db.uow import UnitOfWork
from app.services.classification.rules import ruleManager
from app.services.ml.pipeline import MLPipeline

logger = logging.getLogger(__name__)

UNCATEGORIZED_CATEGORY_ID = 1
CLASSIFICATION_CACHE_TTL_SECONDS = 3600
BATCH_CLASSIFICATION_CONCURRENCY = 10
STRONG_ML_CONFIDENCE_THRESHOLD = 0.95


def _utc_now() -> datetime:
    """Возвращает текущее UTC-время."""
    return datetime.now(timezone.utc)


def _notification_event_id(event_name: str, key: UUID | str) -> UUID:
    """Создает детерминированный notification event id."""
    return uuid5(NAMESPACE_URL, f"smartbudget:notifications:{event_name}:{key}")


def _notification_event(
    event_name: str,
    user_id: UUID,
    payload: dict[str, Any],
    event_id: UUID,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Формирует notification event envelope."""
    event_payload = NotificationPayload(
        user_id=user_id,
        payload=payload,
    )
    event = EventEnvelope.create(
        event_id=event_id,
        event_type=event_name,
        source_service=EventSource.CLASSIFICATION,
        payload=event_payload,
        occurred_at=_utc_now(),
        idempotency_key=idempotency_key,
    )

    return event.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=True,
    )


def _decimal_to_float(value: Decimal | int | float | None) -> float:
    """Безопасно приводит число к float для notification payload."""
    if value is None:
        return 0.0

    return float(value)


def _classification_cache_key(user_id: UUID, transaction_id: UUID) -> str:
    """Возвращает Redis cache key результата классификации."""
    return f"classification:{user_id}:{transaction_id}"


def _classification_completed_event(
    *,
    transaction_id: UUID,
    user_id: UUID,
    category_id: int,
    category_name_snapshot: str,
    confidence: float,
    source: str,
) -> dict[str, Any]:
    """Формирует transaction.classified event envelope."""
    payload = ClassificationCompletedPayload(
        transaction_id=transaction_id,
        user_id=user_id,
        category_id=category_id,
        category_name_snapshot=category_name_snapshot,
        confidence=confidence,
        source=source,
    )
    event = EventEnvelope.create(
        event_type="transaction.classified",
        source_service=EventSource.CLASSIFICATION,
        payload=payload,
        idempotency_key=f"transaction.classified:{transaction_id}",
    )

    return event.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=True,
    )


def _classification_updated_event(
    *,
    transaction_id: UUID,
    user_id: UUID,
    merchant: str | None,
    mcc: int | None,
    description: str | None,
    old_category_id: int | None,
    old_category_name: str | None,
    new_category_id: int,
    new_category_name: str,
) -> dict[str, Any]:
    """Формирует transaction.category_updated event envelope."""
    payload = ClassificationUpdatedPayload(
        transaction_id=transaction_id,
        user_id=user_id,
        merchant=merchant,
        mcc=mcc,
        description=description,
        old_category_id=old_category_id,
        old_category_name=old_category_name,
        new_category_id=new_category_id,
        new_category_name=new_category_name,
    )
    event = EventEnvelope.create(
        event_type="transaction.category_updated",
        source_service=EventSource.CLASSIFICATION,
        payload=payload,
        idempotency_key=f"transaction.category_updated:{transaction_id}",
    )

    return event.model_dump(
        mode="json",
        by_alias=True,
        exclude_none=True,
    )


def _result_to_response(
    result: ClassificationResult,
) -> api_schemas.CategorizationResultResponse:
    """Преобразует ORM-модель результата классификации в API response."""
    return api_schemas.CategorizationResultResponse(
        transaction_id=result.transaction_id,
        category_id=result.category_id,
        category_name_snapshot=result.category_name_snapshot,
        confidence=result.confidence,
        source=result.source.value,
        model_version=result.model_version,
    )


class ClassificationService:
    """Сервис классификации транзакций."""

    def __init__(
        self,
        uow: UnitOfWork,
        redis: Redis,
        ml_pipeline: dict | None = None,
        rules: dict | list[dict] | None = None,
    ) -> None:
        self.uow = uow
        self.redis = redis
        self.ml_pipeline = ml_pipeline
        self.rules = rules or {}

    async def process_batch(
        self,
        events: list[TransactionNeedCategoryEvent],
    ) -> None:
        """Пакетно классифицирует транзакции."""
        if not events:
            return

        tx_ids = [
            event.transaction_id
            for event in events
        ]

        async with self.uow:
            existing_ids = await self.uow.results.get_existing_ids(tx_ids)
            new_events = [
                event
                for event in events
                if event.transaction_id not in existing_ids
            ]

            if not new_events:
                return

            semaphore = asyncio.Semaphore(BATCH_CLASSIFICATION_CONCURRENCY)

            async def classify_with_limit(
                event: TransactionNeedCategoryEvent,
            ) -> tuple[ClassificationResult, dict[str, Any], dict[str, Any] | None]:
                async with semaphore:
                    return await self._calculate_classification(event)

            results_data = await asyncio.gather(
                *[
                    classify_with_limit(event)
                    for event in new_events
                ],
            )

            for result_model, outbox_data, notification_event in results_data:
                await self._save_classification_result(
                    result_model=result_model,
                    outbox_data=outbox_data,
                    notification_event=notification_event,
                )

    async def get_classification(
        self,
        user_id: UUID,
        tx_id: UUID,
    ) -> api_schemas.CategorizationResultResponse:
        """Получает результат классификации по ID транзакции."""
        cache_key = _classification_cache_key(user_id, tx_id)
        cached = await self.redis.get(cache_key)

        if cached:
            return api_schemas.CategorizationResultResponse.model_validate_json(cached)

        async with self.uow:
            result = await self.uow.results.get_user_result(user_id, tx_id)
            if not result:
                raise ClassificationResultNotFoundError("Not found")

            response = _result_to_response(result)
            await self._cache_classification_response(
                user_id=user_id,
                transaction_id=tx_id,
                response=response,
            )

            return response

    async def submit_feedback(
        self,
        user_id: UUID,
        body: api_schemas.FeedbackRequest,
    ) -> tuple[dict[str, Any], Category, dict[str, Any] | None]:
        """Обрабатывает пользовательский feedback по классификации."""
        async with self.uow:
            existing = await self.uow.results.get_user_result(
                user_id,
                body.transaction_id,
            )
            if not existing:
                raise ClassificationResultNotFoundError("Transaction not found")

            correct_category = await self.uow.categories.get_by_id(
                body.correct_category_id,
            )
            if not correct_category:
                raise CategoryNotFoundError("Category not found")

            self._create_feedback(
                user_id=user_id,
                body=body,
            )

            old_category_id = existing.category_id
            old_category_name = existing.category_name_snapshot

            self._apply_manual_category(
                result=existing,
                correct_category=correct_category,
            )

            await self.uow.results.upsert(existing)

            event_data = self._queue_category_updated_event(
                user_id=user_id,
                body=body,
                old_category_id=old_category_id,
                old_category_name=old_category_name,
                correct_category=correct_category,
            )

            notification_event = None
            if old_category_id != body.correct_category_id:
                notification_event = self._queue_category_changed_notification(
                    user_id=user_id,
                    transaction_id=body.transaction_id,
                    old_category_id=old_category_id,
                    new_category_id=body.correct_category_id,
                )

            await self.redis.delete(
                _classification_cache_key(user_id, body.transaction_id),
            )

            return event_data, correct_category, notification_event

    async def classify_transaction(
        self,
        event: TransactionNeedCategoryEvent,
    ) -> None:
        """Классифицирует одну транзакцию из Kafka consumer-а."""
        existing = await self.uow.results.get_by_transaction_id(event.transaction_id)
        if existing:
            return

        result_model, outbox_payload, notification_event = (
            await self._calculate_classification(event)
        )

        await self._save_classification_result(
            result_model=result_model,
            outbox_data=outbox_payload,
            notification_event=notification_event,
        )

    async def _save_classification_result(
        self,
        result_model: ClassificationResult,
        outbox_data: dict[str, Any],
        notification_event: dict[str, Any] | None,
    ) -> None:
        """Сохраняет результат классификации и связанные outbox events."""
        await self.uow.results.upsert(result_model)

        self.uow.outbox.add_event(
            settings.KAFKA.TOPIC_CLASSIFIED,
            outbox_data,
            "transaction.classified",
        )

        if notification_event:
            self.uow.outbox.add_event(
                settings.KAFKA.TOPIC_NOTIFICATION_EVENTS,
                notification_event,
                notification_event.get("event_type", "notification.event"),
            )

        if result_model.user_id:
            await self._cache_classification_response(
                user_id=result_model.user_id,
                transaction_id=result_model.transaction_id,
                response=_result_to_response(result_model),
            )

    async def _calculate_classification(
        self,
        event: TransactionNeedCategoryEvent,
    ) -> tuple[ClassificationResult, dict[str, Any], dict[str, Any] | None]:
        """Рассчитывает категорию транзакции по правилам и ML."""
        merchant = event.merchant
        mcc = event.mcc
        description = event.description or ""

        rule_cat_id, rule_cat_name, rule_type = ruleManager.find_match(
            merchant=merchant,
            mcc=mcc,
            description=description,
        )

        category_id = rule_cat_id
        category_name = rule_cat_name
        source = ClassificationSource.RULES
        confidence = 1.0
        model_version = None

        is_weak_rule = rule_type == "mcc"

        if rule_cat_id is None or is_weak_rule:
            ml_cat_id, ml_cat_name, ml_conf, ml_version = await self._apply_ml(event)

            if ml_cat_id is not None and self._should_use_ml_result(
                rule_cat_id=rule_cat_id,
                ml_cat_id=ml_cat_id,
                ml_confidence=ml_conf,
            ):
                category_id = ml_cat_id
                category_name = ml_cat_name
                source = ClassificationSource.ML
                confidence = ml_conf
                model_version = ml_version

        if category_id is None:
            category_id, category_name, source, confidence = (
                await self._fallback_to_uncategorized()
            )

        result = ClassificationResult(
            transaction_id=event.transaction_id,
            user_id=event.user_id,
            category_id=category_id,
            category_name_snapshot=category_name,
            confidence=confidence,
            source=source,
            model_version=model_version,
            merchant=merchant,
            description=description,
            mcc=mcc,
        )

        outbox_data = _classification_completed_event(
            transaction_id=event.transaction_id,
            user_id=event.user_id,
            category_id=category_id,
            category_name_snapshot=category_name,
            confidence=confidence,
            source=source.value,
        )

        notification_event = self._build_unclassified_notification(
            event=event,
            category_id=category_id,
            confidence=confidence,
        )

        return result, outbox_data, notification_event

    async def _apply_ml(
        self,
        event: TransactionNeedCategoryEvent,
    ) -> tuple[int | None, str | None, float, str | None]:
        """Применяет ML-классификацию к транзакции."""
        if not self.ml_pipeline:
            return None, None, 0.0, None

        model_version = self.ml_pipeline.get("modelVersion")

        try:
            data = {
                "merchant": event.merchant,
                "mcc": event.mcc,
                "description": event.description,
            }
            category_id, confidence = await MLPipeline.predict_async(
                self.ml_pipeline["model"],
                self.ml_pipeline["vectorizer"],
                self.ml_pipeline["classLabels"],
                data,
            )

        except Exception as exc:
            logger.warning(
                "ML classification failed for transaction %s: %s",
                event.transaction_id,
                exc,
                exc_info=True,
            )
            return None, None, 0.0, model_version

        if confidence < settings.ML.ML_CONFIDENCE_THRESHOLD_AUDIT:
            return None, None, confidence, model_version

        category = await self.uow.categories.get_by_id(category_id)
        if not category:
            return None, None, confidence, model_version

        return category_id, category.name, confidence, model_version

    async def _fallback_to_uncategorized(
        self,
    ) -> tuple[int, str, ClassificationSource, float]:
        """Возвращает fallback-категорию, если классификация не дала результата."""
        category = await self.uow.categories.get_by_id(UNCATEGORIZED_CATEGORY_ID)

        return (
            UNCATEGORIZED_CATEGORY_ID,
            category.name if category else "Other",
            ClassificationSource.RULES,
            0.0,
        )

    @staticmethod
    def _should_use_ml_result(
        rule_cat_id: int | None,
        ml_cat_id: int,
        ml_confidence: float,
    ) -> bool:
        """Определяет, можно ли заменить результат правила ML-результатом."""
        return (
            rule_cat_id is None
            or (
                ml_confidence > STRONG_ML_CONFIDENCE_THRESHOLD
                and ml_cat_id != UNCATEGORIZED_CATEGORY_ID
            )
        )

    @staticmethod
    def _build_unclassified_notification(
        event: TransactionNeedCategoryEvent,
        category_id: int,
        confidence: float,
    ) -> dict[str, Any] | None:
        """Формирует notification event для неклассифицированной транзакции."""
        if (
            category_id != UNCATEGORIZED_CATEGORY_ID
            or confidence != 0.0
            or not event.user_id
        ):
            return None

        return _notification_event(
            "transaction.unclassified.found",
            event.user_id,
            {
                "transaction_id": str(event.transaction_id),
                "amount": _decimal_to_float(event.amount),
            },
            event_id=_notification_event_id(
                "transaction.unclassified.found",
                event.transaction_id,
            ),
            idempotency_key=f"transaction.unclassified.found:{event.transaction_id}",
        )

    def _create_feedback(
        self,
        user_id: UUID,
        body: api_schemas.FeedbackRequest,
    ) -> Feedback:
        """Создает feedback-запись."""
        feedback = Feedback(
            transaction_id=body.transaction_id,
            correct_category_id=body.correct_category_id,
            user_id=user_id,
            comment=body.comment,
        )

        return self.uow.feedback.create(feedback)

    @staticmethod
    def _apply_manual_category(
        result: ClassificationResult,
        correct_category: Category,
    ) -> None:
        """Применяет ручную категорию к результату классификации."""
        result.source = ClassificationSource.MANUAL
        result.category_id = correct_category.category_id
        result.category_name_snapshot = correct_category.name
        result.confidence = 1.0

    def _queue_category_updated_event(
        self,
        user_id: UUID,
        body: api_schemas.FeedbackRequest,
        old_category_id: int,
        old_category_name: str,
        correct_category: Category,
    ) -> dict[str, Any]:
        """Добавляет transaction.category_updated event."""
        event_data = _classification_updated_event(
            transaction_id=body.transaction_id,
            user_id=user_id,
            merchant=None,
            mcc=None,
            description=None,
            old_category_id=old_category_id,
            old_category_name=old_category_name,
            new_category_id=body.correct_category_id,
            new_category_name=correct_category.name,
        )

        self.uow.outbox.add_event(
            settings.KAFKA.TOPIC_CATEGORY_UPDATED,
            event_data,
            "transaction.category_updated",
        )

        return event_data

    def _queue_category_changed_notification(
        self,
        user_id: UUID,
        transaction_id: UUID,
        old_category_id: int,
        new_category_id: int,
    ) -> dict[str, Any]:
        """Добавляет notification event изменения категории."""
        notification_event = _notification_event(
            "transaction.category.changed",
            user_id,
            {
                "transaction_id": str(transaction_id),
                "old_category_id": old_category_id,
                "new_category_id": new_category_id,
            },
            event_id=_notification_event_id(
                "transaction.category.changed",
                f"{transaction_id}:{old_category_id}:{new_category_id}",
            ),
            idempotency_key=(
                f"transaction.category.changed:"
                f"{transaction_id}:"
                f"{old_category_id}:"
                f"{new_category_id}"
            ),
        )

        self.uow.outbox.add_event(
            settings.KAFKA.TOPIC_NOTIFICATION_EVENTS,
            notification_event,
            notification_event["event_type"],
        )

        return notification_event

    async def _cache_classification_response(
        self,
        user_id: UUID,
        transaction_id: UUID,
        response: api_schemas.CategorizationResultResponse,
    ) -> None:
        """Кэширует результат классификации в Redis."""
        await self.redis.set(
            _classification_cache_key(user_id, transaction_id),
            response.model_dump_json(),
            ex=CLASSIFICATION_CACHE_TTL_SECONDS,
        )
