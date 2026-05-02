# Transactions Service

FastAPI-сервис транзакций.

## API

Базовый префикс: `/api/v1/transactions`.

- `GET /` - список транзакций пользователя по `X-User-Id`
- `GET /search` - поиск по merchant/description
- `GET /{transaction_id}` - транзакция по `transactionId`
- `POST /manual` - ручное создание транзакции
- `POST /import/mock` - импорт одного объекта или массива транзакций
- `PATCH /edit/{transaction_id}` - смена категории, принимает `{ "categoryId": 2 }`, число или `null`
- `DELETE /edit/{transaction_id}` - удаление транзакции
- `GET /goals/{account_id}` - агрегация транзакций цели по месяцам
- `GET /health`, `/health/live`, `/health/ready` - health checks

Пользовательские операции фильтруются по `X-User-Id`, который выставляет
API Gateway. Если `POST /import/mock` вызывается с `X-User-Id`, сервис
привязывает импорт к этому пользователю и отклоняет body с чужим `userId`.

## Kafka

Публикует:

- `transaction.new`
- `transaction.imported`
- `transaction.goal`
- `transaction.need_category`
- `transaction.updated`
- `transaction.deleted`
- `budget.transactions.events`
- `notification.events` для ручной смены категории

Потребляет:

- `transaction.classified`
- `transaction.updated` от classification feedback

## Переменные окружения

```env
DB__DB_URL=postgresql+asyncpg://postgres:password@transactions_postgres:5432/transactions_db
KAFKA__KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA__KAFKA_GROUP_ID=transactions-service
APP__GOAL_CATEGORY_ID=24
KAFKA__KAFKA_TOPIC_NOTIFICATION_EVENTS=notification.events
```

## Локальный запуск

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Отдельный consumer при необходимости:

```bash
python -m app.run_consumer
```

В `infra/compose/docker-compose.yaml` consumer запускается отдельным
контейнером `transactions_consumer`, как в других Python-сервисах проекта.
