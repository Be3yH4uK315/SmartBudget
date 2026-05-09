# Сервис Целей (Goals Service)

Микросервис управления финансовыми целями для проекта SmartBudget. Обеспечивает создание целей сбережения, отслеживание прогресса, расчет рекомендуемых платежей и уведомление пользователей о ходе выполнения целей.

## 📋 Содержание

- [Обзор](#обзор)
- [Технологический стек](#технологический-стек)
- [Архитектура](#архитектура)
- [Требования](#требования)
- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [Запуск](#запуск)
- [API Эндпоинты](#api-эндпоинты)
- [Kafka События](#kafka-события)
- [Структура проекта](#структура-проекта)
- [Разработка](#разработка)
- [Docker](#docker)
- [Решение проблем](#решение-проблем)

## �� Обзор

Сервис целей отвечает за:

### Управление Целями
- ✅ Создание новых финансовых целей с целевой суммой и датой завершения
- ✅ Отслеживание текущего прогресса по каждой цели
- ✅ Получение списка всех целей пользователя
- ✅ Получение целей для главного экрана (с дополнительной информацией)
- ✅ Удаление и обновление целей
- ✅ Категоризация целей через теги

### Расчеты и Аналитика
- ✅ Автоматический расчет рекомендуемого ежемесячного платежа
- ✅ Расчет дней до завершения цели
- ✅ Расчет процента выполнения цели
- ✅ Расчет остатка до целевой суммы

### Интеграции
- ✅ Потребление событий транзакций из сервиса Classification
- ✅ Автоматическое обновление прогресса по целям при новых транзакциях
- ✅ Отправка событий в Kafka о выполнении целей
- ✅ Обработка ошибок с отправкой в Dead Letter Queue (DLQ)
- ✅ Асинхронные уведомления через Arq

### Надежность
- ✅ Kafka консьюмер с батчингом для оптимальной обработки
- ✅ Обработка ошибок с fallback в DLQ
- ✅ Сохраняемые точки для восстановления после сбоев
- ✅ Health check с проверкой БД и Redis

## 🛠 Технологический стек

| Компонент | Версия | Назначение |
|-----------|--------|-----------|
| **Python** | 3.12 | Язык программирования |
| **FastAPI** | Latest | Асинхронный web framework |
| **SQLAlchemy** | Latest | ORM с асинхронной поддержкой |
| **PostgreSQL** | 16 | Основная база данных |
| **Redis** | 7+ | Очередь Arq, кэширование |
| **Kafka** | 7.5.0 | Event streaming |
| **Arq** | 0.26.3 | Асинхронная очередь задач |
| **Prometheus** | Latest | Метрики и мониторинг |
| **Alembic** | Latest | Миграции БД |

## 🏗 Архитектура

### Слои приложения

```
┌─────────────────────────────────────────┐
│          API Клиент / Фронтенд           │
└────────────────┬────────────────────────┘
                 │
        ┌────────▼──────────┐
        │   FastAPI App      │
        │ ┌────────────────┐ │
        │ │ API Routes     │ │
        │ ├────────────────┤ │
        │ │ Services       │ │
        │ ├────────────────┤ │
        │ │ Repositories   │ │
        │ └────────────────┘ │
        └────────┬───────────┘
                 │
    ┌────────────┼──────────────┬──────────────┐
    │            │              │              │
   ▼            ▼              ▼              ▼
PostgreSQL   Redis            Kafka          Arq
(Goals)     (Arq Queue)   (Events from    (Tasks:
                           Classification) notifications)
```

### Компоненты

1. **API Layer** (`api/routes.py`)
   - FastAPI маршруты для всех эндпоинтов
   - Валидация запросов/ответов через Pydantic schemas
   - Dependency injection для сервисов

2. **Service Layer** (`services/service.py`)
   - Бизнес-логика управления целями
   - Расчет метрик и рекомендаций
   - Создание Kafka событий

3. **Repository Layer** (`infrastructure/db/repositories/`)
   - CRUD операции с целями
   - Outbox репозиторий для Kafka событий
   - Unit of Work паттерн для транзакций
   - SQLAlchemy ORM запросы

4. **Infrastructure Layer** (`infrastructure/`)
   - Kafka Consumer для обработки событий транзакций
   - Kafka Producer для отправки событий
   - Работа с Redis через Arq

5. **Core Layer** (`core/`)
   - Конфигурация и настройки
   - Логирование
   - Исключения
   - Инициализация БД

## 📋 Требования

### Системные
- Python 3.12+
- Docker & Docker Compose (для локального развития)
- 2+ GB RAM, 500MB свободного места

### Внешние сервисы
- PostgreSQL 16+
- Redis 7+
- Apache Kafka 7.5.0+ с Zookeeper
- Сервис Authentication (для верификации пользователя)
- Сервис Classification (для событий транзакций)

## 📦 Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/4y8a4ek/SmartBudget.git
cd SmartBudget/services/goals
```

### 2. Создание виртуального окружения

```bash
# Unix/MacOS
python3.12 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Создание и применение миграций БД

```bash
# Создать новую миграцию (если нужно)
alembic revision --autogenerate -m "Initial schema"

# Применить миграции
alembic upgrade head
```

## 🔐 Конфигурация

### Переменные окружения (.env)

Файл `.env` содержит следующие переменные:

```bash
# --- База данных PostgreSQL
DB__DB_URL=postgresql+asyncpg://postgres:password@localhost:5432/goals_db
DB__DB_POOL_SIZE=20
DB__DB_MAX_OVERFLOW=10

# --- Kafka Topics
KAFKA__KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA__KAFKA_GOALS_GROUP_ID=goals-group
KAFKA__KAFKA_TOPIC_TRANSACTION_GOAL=transaction.goal
KAFKA__KAFKA_TOPIC_BUDGET_EVENTS=budget.goals.events
KAFKA__KAFKA_TOPIC_BUDGET_NOTIFICATION=budget.notification
KAFKA__KAFKA_TOPIC_TRANSACTION_DLQ=goals.transaction.dlq

# --- Redis Arq
ARQ__REDIS_URL=redis://localhost:6379/0
ARQ__ARQ_QUEUE_NAME=goals_tasks

# --- Приложение
APP__LOG_LEVEL=INFO
APP__TZ=UTC
APP__FRONTEND_URL=http://127.0.0.1:3000
```

### Переменные из infra/.env

```bash
# Zookeeper
ZOOKEEPER_CLIENT_PORT=2181
ZOOKEEPER_TICK_TIME=2000

# Kafka
KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1
KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1
ALLOW_PLAINTEXT_LISTENER=yes

# Goals PostgreSQL
GOALS_POSTGRES_USER=postgres
GOALS_POSTGRES_PASSWORD=password
GOALS_POSTGRES_DB=goals_db
```

## 🚀 Запуск

### Локальная разработка с Docker Compose

```bash
# Запустить все сервисы (goals, postgres, redis, kafka, zookeeper)
docker-compose up -d

# Просмотр логов
docker-compose logs -f goals_service

# Остановка
docker-compose down
```

### Локальная разработка без Docker (требует запущенных БД)

```bash
# Терминал 1: FastAPI сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002

# Терминал 2: Kafka Consumer (обработка событий транзакций)
python app/run_consumer.py

# Терминал 3: Arq Worker (фоновые задачи)
arq app.workers.main.WorkerSettings --watch

# Доступ к API
# http://localhost:8002/api/v1/goals/docs (Swagger)
```

### Production с Gunicorn

```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

## 📚 API Эндпоинты

### Interactive Docs
- **Swagger UI**: http://localhost:8002/api/v1/goals/docs
- **ReDoc**: http://localhost:8002/api/v1/goals/redoc

### Health Check

```
GET /api/v1/goals/health
Проверка доступности сервиса и его компонентов

Response: {
  "status": "ok",
  "components": {
    "db": "ok",
    "redis": "ok"
  }
}
```

### Создание Цели

```
POST /api/v1/goals/
Создание новой финансовой цели

Headers: X-User-Id: {user_id}
Body: {
  "name": "Отпуск на Мальдивы",
  "target_value": 100000.00,
  "finish_date": "2025-12-31",
  "tags": ["travel", "vacation"]
}

Response: {
  "goal_id": "uuid",
  "user_id": "uuid",
  "name": "Отпуск на Мальдивы",
  "target_value": 100000.00,
  "current_value": 0.00,
  "finish_date": "2025-12-31",
  "status": "ONGOING",
  "tags": ["travel", "vacation"],
  "created_at": "2026-01-10T..."
}
```

### Получение Целей Главного Экрана

```
GET /api/v1/dashboard/goals
Получение целей для главного экрана с дополнительной информацией

Headers: X-User-Id: {user_id}

Response: {
  "goals": [
    {
      "goal_id": "uuid",
      "name": "Отпуск на Мальдивы",
      "target_value": 100000.00,
      "current_value": 25000.00,
      "finish_date": "2025-12-31",
      "status": "ONGOING",
      "days_left": 356,
      "percentage_complete": 25,
      "recommended_payment": 195.89,
      "tags": ["travel"]
    }
  ]
}
```

### Получение Списка Всех Целей

```
GET /api/v1/goals/
Получение полного списка целей пользователя

Headers: X-User-Id: {user_id}

Response: [
  {
    "goal_id": "uuid",
    "name": "Отпуск на Мальдивы",
    "target_value": 100000.00,
    "current_value": 25000.00,
    "finish_date": "2025-12-31",
    "status": "ONGOING",
    "percentage_complete": 25,
    "tags": ["travel"]
  }
]
```

### Получение Цели по ID

```
GET /api/v1/goals/{goal_id}
Получение информации о конкретной цели

Headers: X-User-Id: {user_id}

Response: {
  "goal_id": "uuid",
  "name": "Отпуск на Мальдивы",
  "target_value": 100000.00,
  "current_value": 25000.00,
  "finish_date": "2025-12-31",
  "status": "ONGOING",
  "percentage_complete": 25,
  "tags": ["travel"],
  "created_at": "2026-01-10T...",
  "updated_at": "2026-01-10T..."
}
```

### Обновление Цели

```
PATCH /api/v1/goals/{goal_id}
Обновление параметров цели

Headers: X-User-Id: {user_id}
Body: {
  "name": "Отпуск в Таиланде",
  "target_value": 80000.00,
  "finish_date": "2025-11-30",
  "tags": ["travel", "asia"]
}

Response: { успешно обновлено }
```

### Удаление Цели

```
DELETE /api/v1/goals/{goal_id}
Удаление цели

Headers: X-User-Id: {user_id}

Response: 204 No Content
```

## 📨 Kafka События

### Потребление Событий

Сервис Goals потребляет события из Classification сервиса:

| Topic | Event Type | Описание |
|-------|-----------|---------|
| `transaction.goal` | Transaction | Транзакция, относящаяся к цели |
| `budget.goals.events` | Budget Goals Event | Событие о ходе цели |
| `budget.notification` | Notification | Уведомление о цели |

### Обработка Событий Транзакций

Когда приходит событие транзакции:
1. Парсится JSON с данными транзакции
2. Находится соответствующая цель по goal_id
3. Обновляется current_value цели
4. Проверяется статус (если достигнута целевая сумма → ACHIEVED)
5. Отправляется событие о выполнении цели
6. При ошибке событие отправляется в DLQ (Dead Letter Queue)

### Отправка Событий

```python
# Событие при создании цели
{
  "event_type": "goal.created",
  "goal_id": "uuid",
  "user_id": "uuid",
  "name": "Отпуск",
  "target_value": 100000.00,
  "finish_date": "2025-12-31"
}

# Событие при достижении цели
{
  "event_type": "goal.achieved",
  "goal_id": "uuid",
  "user_id": "uuid",
  "name": "Отпуск",
  "achieved_at": "2026-01-10T..."
}

# Событие при обновлении прогресса
{
  "event_type": "goal.progress_updated",
  "goal_id": "uuid",
  "user_id": "uuid",
  "current_value": 50000.00,
  "percentage_complete": 50,
  "updated_at": "2026-01-10T..."
}
```

## 📁 Структура проекта

```
goals/
├── app/
│   ├── __init__.py
│   ├── main.py                         # Entry point, lifespan, инициализация
│   ├── run_consumer.py                 # Запуск Kafka consumer
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py             # Dependency injection (get_db, services)
│   │   └── routes.py                   # Все API endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                   # Pydantic Settings, конфигурация
│   │   ├── database.py                 # SQLAlchemy engine, session factory
│   │   ├── exceptions.py               # Кастомные исключения
│   │   └── logging.py                  # Настройка логирования
│   ├── domain/
│   │   └── schemas/                    # Pydantic модели (api, kafka)
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── base.py                 # Base ORM model
│   │   │   ├── models.py               # SQLAlchemy models (Goal, etc)
│   │   │   ├── repositories/           # CRUD/outbox repositories
│   │   │   └── uow.py                  # Unit of Work паттерн
│   │   └── kafka/
│   │       ├── consumer.py             # Kafka consumer для обработки событий
│   │       └── producer.py             # Kafka producer для отправки событий
│   ├── services/
│   │   └── service.py                  # GoalService с бизнес-логикой
│   ├── utils/
│   │   └── serialization.py            # JSON сериализация (decimal, date)
│   └── workers/
│       ├── main.py                     # Arq WorkerSettings
│       └── tasks.py                    # Background задачи
├── alembic/
│   ├── versions/                       # Миграции БД
│   ├── env.py                          # Конфигурация Alembic
│   ├── script.py.mako                  # Шаблон новых миграций
│   └── README
├── .dockerignore                       # Файлы игнорируемые Docker
├── .env                                # Переменные окружения
├── .gitignore                          # Файлы игнорируемые Git
├── alembic.ini                         # Конфигурация Alembic
├── Dockerfile                          # Docker образ
├── docker-compose.yml                  # Docker Compose для локальной разработки
├── requirements.txt                    # Python зависимости
└── README.md                           # Этот файл
```

## 🔧 Разработка

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=app tests/

# Конкретный тест
pytest tests/test_goals_routes.py::test_create_goal
```

### Форматирование и линтинг кода

```bash
# Black - форматирование
black app/

# Flake8 - линтинг
flake8 app/

# Isort - сортировка импортов
isort app/

# MyPy - type checking (если конфигурирован)
mypy app/
```

### Создание миграций БД

```bash
# Автогенерировать миграцию на основе изменений моделей
alembic revision --autogenerate -m "Add new goal field"

# Применить миграции до последней версии
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1

# Откатить на конкретную версию
alembic downgrade <revision_id>
```

### Работа с Kafka локально

```bash
# Создать topic для целей
docker exec kafka kafka-topics --create \
  --topic transaction.goal \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1

# Создать DLQ topic
docker exec kafka kafka-topics --create \
  --topic goals.transaction.dlq \
  --bootstrap-server localhost:9092 \
  --partitions 1 \
  --replication-factor 1

# Слушать сообщения в topic
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic transaction.goal \
  --from-beginning

# Отправить тестовое сообщение
docker exec kafka kafka-console-producer \
  --broker-list localhost:9092 \
  --topic transaction.goal << 'EOF'
{
  "goal_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": 1000.00,
  "timestamp": "2026-01-10T12:00:00Z"
}
EOF
```

## 🐳 Docker

### Сборка образа

```bash
docker build -t smartbudget-goals:latest .
```

### Запуск контейнера

```bash
docker run -p 8002:8000 \
  --env-file .env \
  --name goals-service \
  smartbudget-goals:latest
```

### Docker Compose файл включает

```
services:
  goals_service      - FastAPI приложение
  goals_postgres     - PostgreSQL БД (порт 5436)
  redis_cache        - Redis для Arq
  kafka              - Kafka broker
  zookeeper          - Zookeeper для Kafka

networks:
  smartbudget-net    - Общая сеть для микросервисов

volumes:
  pg_data_goals      - Персистентное хранилище БД
  redis_data_cache   - Персистентное хранилище Redis
```

## �� Решение проблем

### Ошибка: Не могу подключиться к PostgreSQL

```
Error: asyncpg.exceptions.CannotConnectNowError: server closed the connection unexpectedly
```

**Решение:**
```bash
# Проверить что Postgres запущен и миграции применены
docker-compose logs goals_postgres

# Применить миграции
alembic upgrade head

# Если проблема в docker-compose, пересоздать контейнер
docker-compose down
docker-compose up -d
```

### Ошибка: Redis недоступен

```
Error: ConnectionError: Error 111 connecting to localhost:6379
```

**Решение:**
```bash
# Проверить что Redis запущен
redis-cli ping  # должен ответить PONG

# Если Docker Compose используется
docker-compose ps  # проверить статус redis_cache

# Перезапустить Redis
docker-compose restart redis_cache
```

### Ошибка: Миграции не применяются

```
alembic upgrade head
Error: Can't find [alembic] in ./alembic directory
```

**Решение:**
```bash
# Очистить кэш
rm -rf alembic/__pycache__

# Переприменить миграции
alembic upgrade head
```

### Kafka Consumer не обрабатывает события

```
ERROR: Consumer failed to fetch messages
```

**Проверить:**
1. Kafka и Zookeeper запущены: `docker-compose ps`
2. Topic создан: `docker exec kafka kafka-topics --list --bootstrap-server localhost:9092`
3. Consumer запущен: `python app/run_consumer.py`
4. Логи Consumer: `docker-compose logs goals_service`

**Решение:**
```bash
# Перезапустить consumer
docker-compose restart goals_service

# Или вручную
kill $(lsof -t -i :8002)
python app/run_consumer.py
```

### Задачи Arq не выполняются

```
ERROR: Arq queue tasks not processing
```

**Проверить:**
1. Arq Worker запущен
2. Redis доступен
3. Логи Worker: `docker-compose logs goals_worker`

**Решение:**
```bash
# Перезапустить worker
docker-compose restart goals_worker

# Или вручную в отдельном терминале
arq app.workers.main.WorkerSettings --watch
```

## 📊 Мониторинг

### Prometheus метрики

```
http://localhost:8000/metrics
```

Доступные метрики:
- `http_requests_total` - всего HTTP запросов
- `http_request_duration_seconds` - время обработки
- `http_exceptions_total` - количество ошибок
- `kafka_messages_processed_total` - обработанные сообщения Kafka
- `kafka_messages_failed_total` - ошибки при обработке Kafka

### Health Check

```bash
curl http://localhost:8002/api/v1/goals/health

# Response:
{
  "status": "ok",
  "components": {
    "db": "ok",
    "redis": "ok"
  }
}
```

## 🔄 Жизненный цикл Цели

### Статусы

```
ONGOING    → Цель активна, идет накопление
ACHIEVED   → Целевая сумма достигнута
EXPIRED    → Дата завершения прошла, цель не достигнута
CANCELLED  → Цель отменена пользователем
```

### Процесс Обновления при Транзакции

```
1. Транзакция от Classification сервиса
   ↓
2. Kafka Consumer получает событие
   ↓
3. Парсинг JSON и валидация
   ↓
4. Поиск цели по goal_id
   ↓
5. Обновление current_value
   ↓
6. Проверка условий (достаточно ли до цели?)
   ↓
7. Возможное изменение статуса
   ↓
8. Сохранение в БД (трансакция)
   ↓
9. Отправка события в Kafka (goal.progress_updated)
   ↓
10. При ошибке → отправка в DLQ
```

## 🤝 Contributing

1. Создайте ветку: `git checkout -b feature/your-feature`
2. Совершите изменения и запушьте: `git push origin feature/your-feature`
3. Создайте Pull Request

## 📄 Лицензия

MIT License. См. LICENSE файл.

## 👥 Команда

Разработано командой SmartBudget.

---

**Версия**: 1.0  
**Последнее обновление**: Январь 2026  
**Поддерживаемый Python**: 3.12+
