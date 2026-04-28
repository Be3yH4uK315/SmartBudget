# Сервис Аутентификации (Authentication Service)

Микросервис управления аутентификацией и авторизацией для проекта SmartBudget. Обеспечивает регистрацию пользователей, верификацию email, управление сессиями, JWT токенами (RS256) и взаимодействием с другими микросервисами через Kafka события.

## 📋 Содержание

- [Обзор](#обзор)
- [Технологический стек](#технологический-стек)
- [Архитектура](#архитектура)
- [Требования](#требования)
- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [Запуск](#запуск)
- [API Эндпоинты](#api-эндпоинты)
- [Структура проекта](#структура-проекта)
- [Разработка](#разработка)
- [Docker](#docker)
- [Решение проблем](#решение-проблем)

## 🎯 Обзор

Сервис аутентификации отвечает за:

### Аутентификация и Авторизация
- ✅ Регистрация пользователей с верификацией email
- ✅ Вход в систему с генерацией JWT токенов (access + refresh)
- ✅ Валидация и рефреш access токенов
- ✅ Управление сессиями пользователей с отслеживанием устройств
- ✅ JWKS эндпоинт для верификации токенов другими сервисами
- ✅ Gateway верификация (для API Gateway)

### Управление Паролями
- ✅ Сброс пароля с отправкой токена на email
- ✅ Смена пароля для аутентифицированных пользователей
- ✅ Хэширование паролей с bcrypt

### Безопасность
- ✅ Rate limiting на критичные эндпоинты
- ✅ GeoIP локализация для отслеживания сессий
- ✅ HTTP-only и Secure cookies для токенов
- ✅ Fingerprinting refresh токенов
- ✅ Отзыв сессий при смене пароля

### Интеграции
- ✅ Kafka события для синхронизации с другими сервисами
- ✅ Асинхронная отправка email через Arq очередь
- ✅ Очистка истекших сессий
- ✅ Метрики Prometheus для мониторинга

## 🛠 Технологический стек

| Компонент | Версия | Назначение |
|-----------|--------|-----------|
| **Python** | 3.12 | Язык программирования |
| **FastAPI** | Latest | Асинхронный web framework |
| **SQLAlchemy** | Latest | ORM с асинхронной поддержкой |
| **PostgreSQL** | 16 | Основная база данных |
| **Redis** | 7+ | Кэширование, rate limiting |
| **Kafka** | 7.5.0 | Event streaming |
| **Arq** | 0.26.3 | Очередь фоновых задач |
| **PyJWT** | Latest | JWT токены (RS256) |
| **Bcrypt** | Latest | Хэширование паролей |
| **GeoIP2** | Latest | Геолокация IP адресов |
| **FastAPI-Limiter** | Latest | Rate limiting |
| **Prometheus** | Latest | Метрики и мониторинг |
| **Uvloop** | 0.19.0+ | Оптимизированный event loop |

## 🏗 Архитектура

### Слои приложения

```
┌─────────────────────────────────────────┐
│          API Gateway / Клиент            │
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
(Users,    (Rate limit,      (Events:    (Background
Sessions)  Tokens)      user.login, etc)  Tasks)
```

### Компоненты

1. **API Layer** (`api/routes.py`)
   - FastAPI маршруты для всех эндпоинтов
   - Валидация запросов/ответов через Pydantic schemas
   - Error handling с кастомными исключениями

2. **Service Layer** (`services/service.py`)
   - Бизнес-логика аутентификации
   - Управление сессиями и токенами
   - Отправка Kafka событий

3. **Repository Layer** (`infrastructure/db/repositories.py`)
   - CRUD операции с пользователями и сессиями
   - SQLAlchemy ORM запросы
   - Unit of Work паттерн

4. **Infrastructure Layer** (`infrastructure/`)
   - Kafka producer для событий
   - Работа с Redis
   - SMTP отправка email

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
- SMTP сервер (Gmail, SendGrid, Mailhog для разработки)

### GeoIP база данных
- Скачать GeoLite2-City.mmdb с https://www.maxmind.com/en/geolite2
- Разместить в `./geoip/` директорию

## 📦 Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/4y8a4ek/SmartBudget.git
cd SmartBudget/services/authentification
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

### 4. Подготовка сертификатов и баз данных

```bash
# GeoIP база данных (опционально для разработки)
mkdir -p geoip
# Скачать GeoLite2-City.mmdb и разместить в geoip/

# JWT ключи (уже в certs/ репозитория)
ls certs/  # jwt-private.pem, jwt-public.pem
```

### 5. Создание и применение миграций БД

```bash
# Создать новую миграцию (если нужно)
alembic revision --autogenerate -m "Initial schema"

# Применить миграции
alembic upgrade head
```

## 🔐 Конфигурация

### Переменные окружения (.env)

Скопируйте `.env.example` и отредактируйте:

```bash
cp .env.example .env
```

### Основные переменные

```bash
# Приложение
ENV=dev                                # dev или prod
LOG_LEVEL=INFO                         # DEBUG, INFO, WARNING, ERROR
TZ=UTC

# --- База данных PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/auth_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0

# --- Redis
REDIS_URL=redis://localhost:6379/0

# --- Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_GROUP_ID=auth-group
KAFKA_AUTH_EVENTS_TOPIC=auth.events

# --- SMTP Email
SMTP_HOST=localhost                    # или smtp.gmail.com
SMTP_PORT=1025                         # 587 для Gmail
SMTP_USER=noreply@smartbudget.com
SMTP_PASS=your_password
SMTP_FROM_EMAIL=noreply@smartbudget.com
SMTP_FROM_NAME=SmartBudget

# --- JWT
JWT_PRIVATE_KEY_PATH=/app/certs/jwt-private.pem
JWT_PUBLIC_KEY_PATH=/app/certs/jwt-public.pem
JWT_ALGORITHM=RS256

# --- GeoIP
GEOIP_DB_PATH=/geoip/GeoLite2-City.mmdb

# --- Frontend
FRONTEND_URL=http://localhost:3000

# --- Prometheus
PROMETHEUS_PORT=9090
```

## 🚀 Запуск

### Локальная разработка с Docker Compose

```bash
# Запустить все сервисы (auth, postgres, redis, kafka, zookeeper)
docker-compose up -d

# Просмотр логов
docker-compose logs -f auth

# Остановка
docker-compose down
```

### Локальная разработка без Docker (требует запущенных БД)

```bash
# Терминал 1: FastAPI сервер
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Терминал 2: Arq Worker (фоновые задачи)
arq app.workers.main.WorkerSettings --watch

# Доступ к API
# http://localhost:8000/api/v1/auth/docs (Swagger)
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
- **Swagger UI**: http://localhost:8000/api/v1/auth/docs
- **ReDoc**: http://localhost:8000/api/v1/auth/redoc

### Регистрация и Верификация Email

```
POST /api/v1/auth/verify-email
Начать регистрацию с верификацией email
Body: { "email": "user@example.com" }

Response: { "status": "success", "action": "sign_up", "detail": "..." }
```

```
GET /api/v1/auth/verify-link?token=xxx&email=xxx&token_type=verification
Валидация ссылки верификации из email
```

```
POST /api/v1/auth/complete-registration
Завершить регистрацию и создать аккаунт
Body: {
  "email": "user@example.com",
  "token": "xxx",
  "password": "SecurePass123!",
  "name": "John Doe",
  "language": "en"
}
Response: { "status": "success", "action": "complete_registration" }
```

### Вход и Выход

```
POST /api/v1/auth/login
Вход в систему, создание сессии и токенов
Body: { "email": "user@example.com", "password": "SecurePass123!" }
Response: {
  "access_token": "eyJ0eXA...",
  "refresh_token": "eyJ0eXA...",
  "user": { "id": "uuid", "email": "...", "name": "..." }
}
```

```
POST /api/v1/auth/logout
Выход из системы, ревок текущей сессии
Headers: Authorization: Bearer {access_token}
```

```
POST /api/v1/auth/refresh
Обновление access токена используя refresh
Response: { "access_token": "...", "refresh_token": "..." }
```

### Пароль

```
POST /api/v1/auth/reset-password
Начать процесс сброса пароля
Body: { "email": "user@example.com" }

POST /api/v1/auth/complete-reset
Завершить сброс пароля
Body: {
  "email": "user@example.com",
  "token": "xxx",
  "new_password": "NewPass123!"
}

POST /api/v1/auth/change-password
Изменить пароль для залогиненного пользователя
Headers: Authorization: Bearer {access_token}
Body: {
  "password": "CurrentPass123!",
  "new_password": "NewPass456!"
}
```

### Управление Сессиями

```
GET /api/v1/auth/me
Получить информацию о текущем пользователе
Headers: Authorization: Bearer {access_token}
Response: { "id": "uuid", "email": "...", "name": "...", "role": 0 }

PATCH /api/v1/auth/language
Обновить язык интерфейса пользователя
Body: { "language": "ru" }
Allowed values: "ru", "en"

GET /api/v1/auth/sessions
Получить список всех активных сессий пользователя
Headers: Authorization: Bearer {access_token}
Response: [
  {
    "session_id": "uuid",
    "device_name": "Chrome on Windows",
    "location": "Moscow, Russia",
    "ip": "192.168.1.1",
    "created_at": "2026-01-10T...",
    "last_activity": "2026-01-10T..."
  }
]

DELETE /api/v1/auth/sessions/{session_id}
Завершить конкретную сессию
Headers: Authorization: Bearer {access_token}

POST /api/v1/auth/sessions/logout-others
Завершить все другие сессии кроме текущей
Headers: Authorization: Bearer {access_token}
```

### Валидация и JWKS

```
POST /api/v1/auth/validate-token
Валидировать JWT токен
Body: { "token": "eyJ0eXA..." }
Response: { "valid": true, "user_id": "uuid" }

GET /api/v1/auth/.well-known/jwks.json
Получить публичные ключи для верификации JWT в других сервисах
Response: {
  "keys": [{
    "kty": "RSA",
    "use": "sig",
    "alg": "RS256",
    "n": "...",
    "e": "AQAB"
  }]
}

GET /api/v1/auth/gateway-verify
Верификация для API Gateway (проверяет access token в cookie)
Response: 200 OK с header X-User-Id

GET /api/v1/auth/health
Health check сервиса
Response: {
  "status": "ok",
  "components": {
    "database": "ok",
    "redis": "ok",
    "kafka": "ok",
    "geoip": "ok"
  }
}
```

## 📁 Структура проекта

```
authentification/
├── app/
│   ├── __init__.py
│   ├── main.py                       # Entry point, lifespan, инициализация
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py           # Dependency injection (get_db, redis, etc)
│   │   ├── middleware.py             # Обработка ошибок, логирование
│   │   └── routes.py                 # Все API endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                 # Pydantic Settings, конфигурация
│   │   ├── database.py               # SQLAlchemy engine, session factory
│   │   ├── exceptions.py             # Кастомные исключения
│   │   └── logging.py                # Настройка логирования
│   ├── domain/
│   │   └── schemas/                  # Pydantic моделиrequest/response
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── base.py               # Base ORM model
│   │   │   ├── models.py             # SQLAlchemy models (User, Session)
│   │   │   ├── repositories.py       # CRUD operations (UserRepo, SessionRepo)
│   │   │   └── uow.py                # Unit of Work паттерн
│   │   └── kafka/
│   │       └── producer.py           # Kafka producer для событий
│   ├── services/
│   │   └── service.py                # AuthService с бизнес-логикой
│   ├── utils/
│   │   ├── crypto.py                 # JWT, bcrypt операции
│   │   ├── email_templates.py        # HTML шаблоны писем
│   │   ├── network.py                # GeoIP, User-Agent парсинг
│   │   ├── redis_keys.py             # Redis ключи (константы)
│   │   └── serialization.py          # JSON сериализация
│   └── workers/
│       ├── main.py                   # Arq WorkerSettings
│       └── tasks.py                  # Background задачи (email, cleanup)
├── alembic/
│   ├── versions/                     # Миграции БД
│   ├── env.py                        # Конфигурация Alembic
│   ├── script.py.mako                # Шаблон новых миграций
│   └── README
├── certs/
│   ├── jwt-private.pem               # RSA приватный ключ для JWT
│   └── jwt-public.pem                # RSA публичный ключ для JWT
├── geoip/                            # Место для GeoLite2-City.mmdb
├── tests/                            # Unit тесты (если есть)
├── .env.example                      # Пример переменных окружения
├── .dockerignore                     # Файлы игнорируемые Docker
├── .gitignore                        # Файлы игнорируемые Git
├── alembic.ini                       # Конфигурация Alembic
├── Dockerfile                        # Docker образ
├── docker-compose.yml                # Docker Compose для локальной разработки
├── requirements.txt                  # Python зависимости
└── README.md                         # Этот файл
```

## 🔧 Разработка

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=app tests/

# Конкретный тест
pytest tests/test_auth_routes.py::test_login
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
alembic revision --autogenerate -m "Add field to users"

# Применить миграции до последней версии
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1

# Откатить на конкретную версию
alembic downgrade <revision_id>
```

### Генерация новых JWT ключей

```bash
# Создать новую пару ключей (если нужны)
openssl genpkey -algorithm RSA -out jwt-private.pem -pkeyopt rsa_keygen_bits:2048
openssl rsa -pubout -in jwt-private.pem -out jwt-public.pem

# Скопировать в certs/
cp jwt-private.pem certs/
cp jwt-public.pem certs/
```

### Работа с Kafka локально

```bash
# Создать topic
docker exec kafka kafka-topics --create \
  --topic auth.events \
  --bootstrap-server localhost:9092 \
  --partitions 1 \
  --replication-factor 1

# Слушать messages в topic
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic auth.events \
  --from-beginning
```

## 🐳 Docker

### Сборка образа

```bash
docker build -t smartbudget-auth:latest .
```

### Запуск контейнера

```bash
docker run -p 8000:8000 \
  --env-file .env \
  --name auth-service \
  smartbudget-auth:latest
```

### Docker Compose файл включает

```
services:
  auth           - FastAPI приложение
  postgres       - PostgreSQL БД
  redis          - Redis кэш
  kafka          - Kafka broker
  zookeeper      - Zookeeper для Kafka
networks:
  smartbudget-net - Общая сеть для микросервисов
volumes:
  postgres-data  - Персистентное хранилище БД
  redis-data     - Персистентное хранилище Redis
```

## 🐛 Решение проблем

### Ошибка: GeoIP база данных не найдена

```
Error: FileNotFoundError: GeoLite2-City.mmdb not found
```

**Решение:**
1. Скачать базу с https://www.maxmind.com/en/geolite2 (требуется бесплатная регистрация)
2. Разместить файл в `./geoip/GeoLite2-City.mmdb`
3. Убедитесь что в `.env` правильный путь: `GEOIP_DB_PATH=/geoip/GeoLite2-City.mmdb`
4. Перезапустить приложение

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

### Ошибка: Не могу подключиться к PostgreSQL

```
Error: asyncpg.exceptions.CannotConnectNowError: server closed the connection unexpectedly
```

**Решение:**
```bash
# Проверить что Postgres запущен и миграции применены
docker-compose logs postgres

# Применить миграции
alembic upgrade head

# Если проблема в docker-compose, пересоздать контейнер
docker-compose down
docker-compose up -d
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

# Пересоздать миграции
alembic init alembic

# Применить
alembic upgrade head
```

### Email не отправляется

**Проверить:**
1. SMTP переменные в `.env` верны
2. Сервис Arq запущен в отдельном терминале
3. Логи Arq Worker: `docker-compose logs auth-worker`

```bash
# Для разработки использовать Mailhog (видны все письма в UI)
# Запустить в docker-compose.yml и открыть http://localhost:1025
```

### Kafka события не обрабатываются

**Проверить:**
1. Kafka и Zookeeper запущены: `docker-compose ps`
2. Topic создан: `docker exec kafka kafka-topics --list --bootstrap-server localhost:9092`
3. Логи: `docker-compose logs kafka`

## 📊 Мониторинг

### Prometheus метрики

```
http://localhost:9090/metrics
```

Доступные метрики:
- `http_requests_total` - всего HTTP запросов
- `http_request_duration_seconds` - время обработки
- `http_exceptions_total` - количество ошибок
- `auth_login_attempts_total` - попытки входа
- `auth_failed_logins_total` - неудачные входы

### Health Check

```bash
curl http://localhost:8000/api/v1/auth/health

# Response:
{
  "status": "ok",
  "components": {
    "database": "ok",
    "redis": "ok",
    "kafka": "ok",
    "geoip": "available"
  }
}
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
