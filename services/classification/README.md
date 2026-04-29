# Сервис: Classification

Микросервис автоматической категоризации транзакций в системе SmartBudget. Использует гибридный подход: LightGBM-модели для ML-предсказаний и rule-based движок для точных матчей. Интегрирован с Kafka для асинхронной обработки, использует Redis для кэширования результатов и OpenTelemetry для распределённой трассировки.

**Цель README**: полное описание архитектуры, конфигурации, запуска, API, интеграции и мониторинга.

---

## Содержание

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Архитектура](#архитектура)
- [Конфигурация](#конфигурация)
- [Установка и запуск](#установка-и-запуск)
- [API](#api)
- [Kafka Topics](#kafka-topics)
- [ML Pipeline](#ml-pipeline)
- [Rule Engine](#rule-engine)
- [Observability](#observability)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Overview

Сервис автоматически классифицирует транзакции по категориям бюджетирования:

1. **Входная точка**: Kafka топик `transaction.need_category` содержит события о транзакциях, требующих категоризации.
2. **Обработка**: Сервис применяет rule-based логику, затем ML-модель (LightGBM) для предсказания.
3. **Выходная точка**: Результаты публикуются в `transaction.classified` с категорией и уровнем доверия.

**Ключевые особенности**:
- **Двойной подход**: правила имеют приоритет (для точных матчей); ML используется как fallback и для предложений.
- **Confidence thresholds**: высокая вероятность → автоматическое принятие; средняя → пометка для аудита.
- **Асинхронная обработка**: через `aiokafka` и Arq.
- **Кэширование**: результаты в Redis.
- **Трассировка**: полная интеграция OpenTelemetry (FastAPI, SQLAlchemy, AIOKafka, Redis, Arq).
- **Метрики**: Prometheus через `prometheus-fastapi-instrumentator`.

---

## Tech Stack

| Компонент | Версия/Технология |
|-----------|-------------------|
| Python | 3.11+ |
| FastAPI | latest |
| БД | PostgreSQL 16 + SQLAlchemy (async) + asyncpg |
| Кэш | Redis 7+ + aioredis |
| Очереди | Kafka 7.5.0 + aiokafka |
| Jobs | Arq 0.26.3 |
| ML | LightGBM + scikit-learn + pandas + pyarrow |
| Observability | OpenTelemetry (API, SDK, OTLP Exporter) |
| Metrics | Prometheus + prometheus-fastapi-instrumentator |

---

## Архитектура

### Структура проекта

```
services/classification/
├── Dockerfile                  # Multi-stage build (libgomp1 для LightGBM)
├── docker-compose.yml          # Локальное окружение (опционально)
├── .env                        # Переменные окружения
├── requirements.txt            # Python зависимости (25+ пакетов)
├── README.md                   # Этот файл
├── alembic/                    # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── app/
│   ├── main.py                 # Входная точка FastAPI + lifespan
│   ├── run_consumer.py         # Запуск Kafka consumer loop
│   ├── api/
│   │   ├── routes.py           # HTTP endpoints (/health, /classification, /feedback, etc)
│   │   └── dependencies.py     # Dependency injection
│   ├── core/
│   │   ├── config.py           # Pydantic Settings (DB, Kafka, ML, ARQ, App)
│   │   ├── database.py         # SQLAlchemy async engine + session factory
│   │   ├── redis.py            # Redis connection pool
│   │   ├── exceptions.py       # Custom exceptions (ClassificationServiceError, ModelLoadError, etc)
│   │   └── logging.py          # Logging configuration
│   ├── services/
│   │   ├── ml/
│   │   │   ├── manager.py      # ModelManager (singleton, in-memory model cache)
│   │   │   └── pipeline.py     # MLPipeline (feature extraction, vectorization, prediction)
│   │   └── classification/
│   │       ├── rules.py        # RuleManager (singleton, rule caching and lookup)
│   │       └── service.py      # ClassificationService (main logic: rules + ML combo)
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── base.py         # Base for ORM models
│   │   │   ├── models.py       # SQLAlchemy models (Category, Rule, ClassificationResult, etc)
│   │   │   ├── repositories/   # Data access layer
│   │   │   └── uow.py          # Unit of Work pattern
│   │   └── kafka/
│   │       ├── consumer.py     # AIOKafka consumer loop (transaction.need_category)
│   │       └── producer.py     # Safe producer wrapper (send to transaction.classified, DLQ, etc)
│   ├── domain/
│   │   └── schemas/
│   │       ├── api.py          # Pydantic models for HTTP requests/responses
│   │       └── kafka.py        # Pydantic models for Kafka messages
│   ├── utils/                  # Utilities
│   └── workers/                # Background job handlers (if Arq is used)
└── datasets/                   # (в контейнере) Датасеты для ML
```

### Поток обработки транзакции

```
1. Kafka Consumer (run_consumer.py)
   ↓
2. Валидация сообщения (TransactionNeedCategoryEvent)
   ↓
3. RuleManager.check_for_updates() + apply_rules()
   ├── Lookup по MCC (точный матч)
   ├── Lookup по exact text (точный матч)
   └── Iterate complex rules (regex)
   ↓
4. Если правило сработало → публикуем результат
   │
   └─ Если нет → ML Pipeline
      ↓
5. ModelManager.get_pipeline() → MLPipeline.predict()
   ├── Feature extraction
   ├── Vectorization
   └── LightGBM prediction → (category, probability)
   ↓
6. Применяем пороги доверия (confidence thresholds)
   ├── probability >= ACCEPT_THRESHOLD → автоматическое принятие
   ├── AUDIT_THRESHOLD <= probability < ACCEPT_THRESHOLD → пометка для аудита
   └── probability < AUDIT_THRESHOLD → manual review
   ↓
7. Кэшируем результат в Redis
   ↓
8. Публикуем в transaction.classified
   ↓
9. Подтверждаем оффсет (manual commit, enable_auto_commit=False)
```

---

## Конфигурация

### Переменные окружения (из `.env`)

Все переменные читаются через Pydantic `BaseSettings` с вложенной структурой (`env_nested_delimiter="__"`).

#### Database

```env
DB__DB_URL=postgresql+asyncpg://user:password@localhost:5432/classification_db
DB__DB_POOL_SIZE=20
DB__DB_MAX_OVERFLOW=10
```

#### Redis & Arq

```env
ARQ__REDIS_URL=redis://localhost:6379/1
ARQ__ARQ_QUEUE_NAME=classification_tasks
ARQ__REDIS_MAX_CONNECTIONS=10
```

#### Kafka

```env
KAFKA__KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA__KAFKA_GROUP_ID=classification-group
KAFKA__TOPIC_NEED_CATEGORY=transaction.need_category
KAFKA__TOPIC_CLASSIFIED=transaction.classified
KAFKA__TOPIC_UPDATED=transaction.updated
KAFKA__TOPIC_CLASSIFICATION_EVENTS=budget.classification.events
```

#### ML

```env
ML__MODEL_PATH=/app/ml_models
ML__DATASET_PATH=/app/datasets
ML__ML_CONFIDENCE_THRESHOLD_ACCEPT=0.8
ML__ML_CONFIDENCE_THRESHOLD_AUDIT=0.4
```

#### Application

```env
APP__ENV=development
APP__FRONTEND_URL=http://localhost:3000
APP__PROMETHEUS_PORT=8001
APP__LOG_LEVEL=INFO
APP__TZ=UTC
```

**Важно**: точные имена переменных и структура находятся в `app/core/config.py` — используйте как единственный источник правды.

---

## Установка и запуск

### Локально через docker-compose

```bash
cd services/classification
docker compose up --build
```

Это поднимает: FastAPI сервис (8001), PostgreSQL (5432), Redis (6379), Kafka (9092).

### Локально без контейнеризации

```bash
# Убедитесь, что работают Postgres, Redis, Kafka

cd services/classification
python -m venv .venv
source .venv/bin/activate  # или: .venv\Scripts\activate на Windows
pip install -r requirements.txt

# Экспортируем переменные окружения
export $(cat .env | xargs)

# Запуск FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# В другом терминале: запуск Kafka consumer
python -m app.run_consumer
```

### Docker

```bash
docker build -t smartbudget-classification:latest .
docker run \
  --env-file .env \
  -p 8001:8001 \
  -v $(pwd)/ml_models:/app/ml_models \
  smartbudget-classification:latest
```

**Примечание**: Dockerfile имеет multi-stage build и устанавливает `libgomp1` (требуется для LightGBM).

---

## API

### Endpoints

#### Health Check

```http
GET /health
```

Проверяет доступность DB и Redis.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "details": {
    "db": "ok",
    "redis": "ok"
  }
}
```

#### Получить результат классификации

```http
GET /classification/{transaction_id}
```

**Path Parameters**:
- `transaction_id` (UUID): ID транзакции

**Response** (200 OK):
```json
{
  "transactionId": "550e8400-e29b-41d4-a716-446655440000",
  "categoryId": 123,
  "categoryName": "Groceries",
  "confidence": 0.92,
  "source": "rule-based",
  "timestamp": "2026-01-10T12:00:00Z",
  "metadata": {}
}
```

**Response** (404 Not Found):
```json
{
  "detail": "Classification result not found for transaction 550e8400-e29b-41d4-a716-446655440000"
}
```

#### Отправить feedback

```http
POST /feedback
```

**Body** (Pydantic `FeedbackRequest`):
```json
{
  "transactionId": "550e8400-e29b-41d4-a716-446655440000",
  "categoryId": 123,
  "feedbackType": "correct",
  "comment": "Great classification!"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Feedback received"
}
```

### OpenAPI Documentation

- **Swagger UI**: `/api/v1/class/docs`
- **ReDoc**: `/api/v1/class/redoc`
- **OpenAPI JSON**: `/api/v1/class/openapi.json`

Точные маршруты зависят от конфигурации `app/api/routes.py`.

---

## Kafka Topics

### Структура сообщений

#### transaction.need_category (входящий топик)

```json
{
  "transactionId": "550e8400-e29b-41d4-a716-446655440000",
  "amount": 50.00,
  "description": "STARBUCKS COFFEE",
  "merchantMCC": "5812",
  "userId": "user-123",
  "timestamp": "2026-01-10T12:00:00Z",
  "metadata": {}
}
```

#### transaction.classified (исходящий топик)

```json
{
  "transactionId": "550e8400-e29b-41d4-a716-446655440000",
  "categoryId": 123,
  "categoryName": "Food & Drink",
  "confidence": 0.95,
  "source": "rule-based",
  "timestamp": "2026-01-10T12:00:01Z"
}
```

#### budget.classification.events (аудит-топик)

```json
{
  "eventType": "classification_completed",
  "transactionId": "550e8400-e29b-41d4-a716-446655440000",
  "categoryId": 123,
  "confidence": 0.95,
  "source": "ml",
  "timestamp": "2026-01-10T12:00:01Z",
  "processingTimeMs": 42
}
```

### Dead Letter Queue (DLQ)

При критической ошибке (например, невалидное сообщение) оно отправляется в DLQ:

```
transaction.need_category.dlq
```

```json
{
  "originalTopic": "transaction.need_category",
  "originalMessage": "{...}",
  "error": "Validation error: ...",
  "timestamp": "2026-01-10T12:00:02Z"
}
```

---

## ML Pipeline

### ModelManager

**Описание**: Singleton для управления ML-моделью в памяти.

**Функционал**:
- Загрузка модели при старте приложения (в `app/main.py` lifespan).
- Periodic check (каждые 60 сек) для обновлений модели из БД.
- Атомарное сохранение артефактов в `ModelArtifacts` (frozen dataclass).

**Ключевые методы**:
- `get_pipeline()` → возвращает dict с моделью, векторизатором, лейблами классов и версией.
- `check_for_updates(db_session_maker)` → async метод для периодической проверки обновлений.

**Артефакты модели** (`ModelArtifacts`):
```python
@dataclass(frozen=True)
class ModelArtifacts:
    model: Any                    # LightGBM Booster
    vectorizer: Any              # sklearn TfidfVectorizer
    class_labels: list[int]       # Список ID категорий
    version: str                  # Версия модели (e.g., "1.2.3")
```

### MLPipeline

**Описание**: Реализует предсказание для транзакции.

**Процесс**:
1. Feature extraction из `TransactionNeedCategoryEvent`.
2. Текстовая векторизация (TF-IDF).
3. Передача в LightGBM модель → получаем probability для каждого класса.
4. Выбираем класс с максимальной probability.

**Confidence Thresholds**:
```
if probability >= ML_CONFIDENCE_THRESHOLD_ACCEPT (0.8):
    status = "ACCEPTED"
elif probability >= ML_CONFIDENCE_THRESHOLD_AUDIT (0.4):
    status = "AUDIT"
else:
    status = "MANUAL"
```

### Обновление моделей

1. **Разработка**: Обучить модель офлайн.
2. **Сохранение**: Экспортировать модель (pickle, joblib или ONNX) в `ML__MODEL_PATH`.
3. **Метаданные**: Обновить запись в БД с версией, метриками, датой обучения.
4. **Pickup**: `ModelManager.check_for_updates()` подхватит новую версию.

---

## Rule Engine

### RuleManager

**Описание**: Singleton для управления правилами классификации, загруженными из БД и кэшированными в памяти.

**Типы правил**:
1. **MCC** (Merchant Category Code): точный матч по коду MCC → категория.
2. **Exact**: точное совпадение текста описания (case-insensitive, trimmed).
3. **Complex**: регулярные выражения или более сложные паттерны.

**Структура кэша**:
```python
_mcc_rules = {}        # {mcc_code: rule}
_exact_rules = {}      # {lowercase_pattern: rule}
_complex_rules = []    # [rule1, rule2, ...]
```

**Функционал**:
- Periodic check (каждые 30 сек) для обновления правил из БД.
- Применение правил в приоритетном порядке: MCC → Exact → Complex.
- `get_rules()` → возвращает текущие кэшированные правила.

**Пример добавления правила**:
```sql
INSERT INTO classification_rules (pattern_type, mcc, pattern, category_id, priority, active)
VALUES ('mcc', '5812', NULL, 123, 100, true);
```

После этого правило будет автоматически загружено RuleManager.

---

## Observability

### OpenTelemetry

Приложение полностью инструментировано:

- **FastAPI**: трассировка HTTP запросов/ответов.
- **SQLAlchemy**: трассировка SQL запросов.
- **AIOKafka**: трассировка Kafka produce/consume операций.
- **Redis**: трассировка Redis команд.
- **Arq**: трассировка фоновых задач (если используется).

### Prometheus Metrics

Метрики доступны на порту `APP__PROMETHEUS_PORT` (по умолчанию 8001):

```http
GET http://localhost:8001/metrics
```

Ключевые метрики:
- `http_requests_total` — общее количество HTTP запросов.
- `http_request_duration_seconds` — длительность HTTP запросов.
- `kafka_messages_consumed_total` — количество обработанных Kafka сообщений.
- `classification_cache_hits_total` — количество попаданий в кэш.
- `ml_prediction_duration_seconds` — длительность ML предсказания.

### Логирование

Все логи структурированы через модуль `app/core/logging.py`:

```python
logger = logging.getLogger(__name__)
logger.info("Classification completed", extra={"transaction_id": "...", "category": "..."})
```

Уровень логирования контролируется переменной `APP__LOG_LEVEL`.

---

## Troubleshooting

### ML модель не загружается

**Ошибка в логах**: `ModelLoadError: Failed to load model from path ...`

**Решение**:
1. Проверьте `ML__MODEL_PATH` — существует ли файл/директория.
2. Убедитесь, что модель совместима с текущей версией LightGBM.
3. Проверьте права доступа на файлы.

### Consumer падает при отправке в DLQ

**Ошибка в логах**: `CRITICAL: Failed to send to DLQ! Stopping consumer to prevent data loss.`

**Решение**:
1. Проверьте доступность Kafka кластера.
2. Убедитесь, что у сервиса есть права на создание топиков (или топик `transaction.need_category.dlq` уже существует).
3. Проверьте `KAFKA__KAFKA_BOOTSTRAP_SERVERS`.

### Health-check возвращает `unhealthy`

**Response**:
```json
{
  "status": "unhealthy",
  "details": {
    "db": "error: connection timeout",
    "redis": "disconnected"
  }
}
```

**Решение**:
1. Проверьте доступность PostgreSQL на `DB__DB_URL`.
2. Проверьте доступность Redis на `ARQ__REDIS_URL`.
3. Убедитесь, что сервисы запущены и открыты на указанных портах.

### OutOfMemory при обработке больших сообщений

**Решение**:
1. Уменьшите `DB__DB_POOL_SIZE` и `ARQ__REDIS_MAX_CONNECTIONS`.
2. Добавьте больше памяти контейнеру (в docker-compose или Kubernetes).
3. Реализуйте batching при обработке сообщений.

---

## FAQ

**Q: Как добавлять новые правила классификации?**

A: Добавляйте записи в таблицу `classification_rules` (через миграции или UI):
```sql
INSERT INTO classification_rules (pattern_type, mcc, pattern, category_id, priority, active)
VALUES ('exact', NULL, 'AMAZON', 456, 50, true);
```
RuleManager автоматически подхватит активные правила по интервалу (~30 сек).

**Q: Как обновить ML модель без перезапуска?**

A: Сохраните новую версию модели в `ML__MODEL_PATH` и обновите метаданные в БД (таблица `ml_models` или аналог). `ModelManager.check_for_updates()` подхватит новую версию (~60 сек).

**Q: Что делать при очень низкой уверенности ML модели?**

A: 
1. Проверьте качество датасета (может быть неполнота или дисбаланс классов).
2. Пересчитайте пороги доверия (`ML_CONFIDENCE_THRESHOLD_ACCEPT`, `ML_CONFIDENCE_THRESHOLD_AUDIT`).
3. Переобучите модель с новыми параметрами/фичами.

**Q: Как масштабировать сервис?**

A: 
1. Запустите несколько инстансов сервиса за load balancer'ом (Nginx, HAProxy).
2. Для consumer'а: используйте consumer группы Kafka (одна группа, несколько инстансов, автоматическое распределение партиций).
3. Кэш в Redis будет распределён между инстансами (используйте Redis Cluster для HA).

**Q: Можно ли отключить ML и использовать только правила?**

A: Да, в `ClassificationService` модифицируйте логику так, чтобы если правило не сработало, то отправлять сообщение в MANUAL очередь вместо вызова ML.

**Q: Как настроить логирование в продакшене?**

A: 
1. Установите `APP__LOG_LEVEL=WARNING` (или `ERROR` для минимизации).
2. Используйте структурированное логирование (JSON) через `python-json-logger`.
3. Отправляйте логи в централизованное хранилище (ELK, Loki, DataDog, etc).
4. Настройте OpenTelemetry экспортер (OTLP) для Jaeger/Zipkin/Tempo.

---

## Deployment

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: classification-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: classification
        image: smartbudget-classification:latest
        ports:
        - containerPort: 8001
        env:
        - name: DB__DB_URL
          valueFrom:
            secretKeyRef:
              name: classification-secrets
              key: db-url
        # ... остальные переменные
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Monitoring & Alerting

- **Метрики Prometheus**: настройте Prometheus для скрейпа метрик с сервиса.
- **Alerts**: установите alert'ы для `http_request_duration_seconds` > 5s, `kafka_consumer_lag` > 10000, и т.д.
- **Tracing**: подключите Jaeger/Zipkin для анализа распределённых трасс.

---

## Справочные пути

- `app/main.py` — точка входа, lifespan, инициализация сервисов.
- `app/api/routes.py` — HTTP endpoints.
- `app/core/config.py` — конфигурация (источник правды для переменных).
- `app/services/ml/manager.py` — управление моделями.
- `app/services/classification/rules.py` — управление правилами.
- `app/infrastructure/kafka/consumer.py` — Kafka consumer loop.
- `app/infrastructure/db/models.py` — SQLAlchemy модели.
- `app/domain/schemas/` — Pydantic схемы для API и Kafka.

---

## Контакты

- **Архитектура & ML**: Data/ML команда
- **Интеграция & DevOps**: Backend/DevOps команда
- **Мониторинг**: SRE команда

---

**Версия документа**: 1.0
**Последнее обновление**: 10 января 2026
**Автор**: SmartBudget Development Team
