# Budgets Service

FastAPI-сервис бюджетов для SmartBudget. Реализация следует стилю Python-сервисов
`goals` и `transactions`: async SQLAlchemy, Repository + UnitOfWork, Alembic,
Kafka consumer и outbox worker через ARQ.

## API

Базовый префикс: `/api/v1/budget`.

- `GET /` - бюджет пользователя по `X-User-Id`, опционально `?month=YYYY-MM-DD`
- `POST /` - создание бюджета месяца, опционально `?month=YYYY-MM-DD`
- `GET /settings` - настройки бюджета месяца, опционально `?month=YYYY-MM-DD`
- `PATCH /settings` - обновление лимитов и auto-renew месяца, опционально `?month=YYYY-MM-DD`
- `GET /dashboard` - агрегат для `/api/v1/dashboard/budget`, опционально `?month=YYYY-MM-DD`
- `GET /health`, `/health/live`, `/health/ready` - health checks

`POST /` и `PATCH /settings` принимают прямой JSON body по Pydantic-схеме
сервисов FastAPI.

## Kafka

Потребляет:

- `transaction.new`
- `transaction.updated`
- `transaction.deleted`

Публикует через outbox:

- `budget.budgets.events`
- `notification.events` for budget settings notifications

Для корректной обработки `transaction.updated` и `transaction.deleted` сервис
хранит обработанные транзакции в `processed_budget_transactions` вместе с
месяцем бюджета. События `transaction.new`, `transaction.updated` и
`transaction.deleted` используют canonical поля `transaction_id`, `user_id`,
`amount`, `transaction_type` и `occurred_at`; старые сообщения без
`occurred_at` не принимаются.

ARQ worker выполняет:

- outbox delivery loop
- auto-renew бюджетов в первый день месяца

## Переменные окружения

```env
DB__DB_URL=postgresql+asyncpg://postgres:password@budgets_postgres:5432/budgets_db
KAFKA__KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA__KAFKA_GROUP_ID=budgets-service
KAFKA__KAFKA_TOPIC_TRANSACTION_NEW=transaction.new
KAFKA__KAFKA_TOPIC_TRANSACTION_UPDATED=transaction.updated
KAFKA__KAFKA_TOPIC_TRANSACTION_DELETED=transaction.deleted
KAFKA__KAFKA_TOPIC_BUDGET_EVENTS=budget.budgets.events
KAFKA__KAFKA_TOPIC_NOTIFICATION_EVENTS=notification.events
ARQ__REDIS_URL=redis://redis_cache:6379/0
ARQ__ARQ_QUEUE_NAME=budgets_tasks
```

## Локальный запуск

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Отдельный consumer:

```bash
python -m app.run_consumer
```

Отдельный worker outbox:

```bash
arq app.workers.main.WorkerSettings
```
