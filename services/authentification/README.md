# Микросервис Аутентификации (Authentication Service) для Проекта "Умный Бюджет"

## Описание

Микросервис аутентификации является ключевой частью проекта "Умный Бюджет" (Smart Budget), который представляет собой комплексную систему управления личными финансами. Этот сервис отвечает за обработку всех аспектов аутентификации и авторизации пользователей, включая регистрацию, вход, выход, сброс пароля, смену пароля и валидацию токенов. Он построен на базе FastAPI для обеспечения высокой производительности и асинхронной обработки запросов.

### Основные Функции
- **Регистрация пользователей**: Верификация email с отправкой токена, завершение регистрации с созданием аккаунта и сессии.
- **Вход и выход**: Аутентификация по email и паролю, генерация JWT access и refresh токенов, ревок сессий.
- **Сброс и смена пароля**: Отправка токена сброса на email, валидация и обновление пароля.
- **Валидация токенов**: Проверка JWT токенов для интеграции с другими сервисами.
- **Обновление сессий**: Рефреш access токена с использованием refresh токена.
- **JWKS эндпоинт**: Предоставление публичных ключей для валидации JWT в других сервисах.
- **Интеграции**: Отправка событий в Kafka для уведомлений и логов, асинхронные задачи через Arq (email, Kafka события, очистка сессий).
- **Безопасность**: Хэширование паролей с bcrypt, fingerprinting refresh токенов, rate limiting, GeoIP для локаций, HTTP-only cookies для токенов.

Сервис спроектирован с учетом масштабируемости, безопасности и интеграции в микросервисную архитектуру проекта. Он использует PostgreSQL для хранения пользователей и сессий, Redis для кэширования (токены верификации, rate limiting), Kafka для событий и Arq для фоновых задач.

## Требования

### Зависимости
- Python 3.12 или выше.
- Docker и Docker Compose для контейнеризации.
- Установленные библиотеки из `requirements.txt` (FastAPI, SQLAlchemy, Aiokafka, Arq, Redis, PyJWT, Bcrypt и другие).

### Внешние Сервисы
- PostgreSQL 16: Для хранения данных пользователей и сессий.
- Redis 7: Для кэширования и очередей Arq.
- Kafka (с Zookeeper): Для отправки событий (например, "user.registered", "user.login").
- SMTP сервер (например, Mailhog для разработки): Для отправки email.
- GeoIP база данных: Файл GeoLite2-City.mmdb (скачать с MaxMind и разместить в /geoip).

### Окружение
- Разработка: `env=dev`.
- Продакшн: `env=prod` (включает HTTPS, secure cookies).

## Установка

1. **Клонирование Репозитория**:
   Клонируйте основной репозиторий проекта:
```bash
git clone https://github.com/4y8a4ek/SmartBudget.git
cd SmartBudget/services/authentification
```
2. **Установка Зависимостей**:
Создайте виртуальное окружение и установите пакеты:
```bash
python -m venv venv
source venv/bin/activate  # Для Unix/Mac
source venv\Scripts\activate # Для Windows
pip install -r requirements.txt
```
3. **Конфигурация Окружения**:
Создайте файл `.env` в корне сервиса на основе примера (если нет):
```bash
ENV=dev
DB_URL=postgresql+asyncpg://postgres:password@localhost:5433/auth_db
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
REDIS_URL=redis://localhost:6379/0
ARQ_QUEUE_NAME=auth_tasks
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=your_smtp_user
SMTP_PASS=your_smtp_pass
GEOIP_DB_PATH=/geoip/GeoLite2-City.mmdb
```
Скачайте GeoLite2-City.mmdb с [MaxMind](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data) и разместите в `./geoip`.

4. **Генерация JWT Ключей**:
Создайте RSA ключи для JWT:
```bash
mkdir certs
openssl genpkey -algorithm RSA -out certs/jwt-private.pem -pkeyopt rsa_keygen_bits:2048
openssl rsa -pubout -in certs/jwt-private.pem -out certs/jwt-public.pem
```
5. **Миграции БД**:
Инициализируйте и примените миграции с Alembic:
```bash
alembic init migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```
## Запуск

### Локальный Запуск (Без Docker)
1. Запустите внешние сервисы (PostgreSQL, Redis, Kafka, Zookeeper, Mailhog) вручную или через скрипты.
2. Запустите сервер:
```bash
uvicorn app.main:app --reload --port 8000
```
3. Запустите Arq worker отдельно:
```bash
arq app.worker.WorkerSettings
```
### Запуск с Docker Compose
1. Соберите и запустите:
```bash
docker-compose -f docker-compose.yml up -d --build
```
Это запустит: auth_service, auth_postgres_dev, auth_redis_dev, auth_zookeeper_dev, auth_kafka_dev, mailhog, auth_worker.
2. Проверьте логи:
```bash
docker logs auth_service_dev
```
3. Доступ к API: http://localhost:8000 (docs: /docs).
4. Mailhog UI: http://localhost:8025 для просмотра отправленных email.

### Продакшн Запуск
- Используйте `docker-compose.prod.yml` (не включен, но аналогичен dev с secure настройками).
- Установите `ENV=prod` в .env для secure cookies и TLS.
- Масштабируйте workers: `docker-compose scale auth_worker=3`.

## Конфигурация

- **.env**: Все настройки (см. выше).
- **settings.py**: Pydantic для валидации настроек.
- **JWT**: Ключи в /certs; алгоритм RS256.
- **Kafka Schemas**: Определены в kafka.py для валидации событий.
- **Arq Tasks**: Асинхронные задачи для email, Kafka, cleanup сессий (cron ежедневно в 3:00).
- **Rate Limiting**: 5 запросов/минуту для /login и /reset-password.
- **Прометей**: Метрики на /metrics (порт 8001).

## API Эндпоинты

- **POST /verify-email**: Инициирует верификацию email.
- Body: {"email": "user@example.com"}
- **GET /verify-link?token=...&email=...**: Валидирует токен из email.
- **POST /complete-registration**: Завершает регистрацию.
- Body: {"email": "...", "name": "...", "country": "...", "token": "...", "password": "...", "user_agent": "..."}
- **POST /login**: Вход пользователя.
- Body: {"email": "...", "password": "...", "user_agent": "..."}
- **POST /logout**: Выход (ревок сессии).
- **POST /reset-password**: Инициирует сброс пароля.
- Body: {"email": "..."}
- **POST /complete-reset**: Завершает сброс.
- Body: {"email": "...", "token": "...", "new_password": "..."}
- **POST /change-password**: Смена пароля.
- Body: {"user_id": "...", "password": "...", "new_password": "..."}
- **POST /validate-token**: Валидация JWT.
- Body: {"token": "..."}
- **POST /refresh**: Рефреш access токена.
- Body: {"refresh_token": "..."}
- **GET /.well-known/jwks.json**: JWKS для публичных ключей.

Все эндпоинты возвращают JSON с куки (access_token, refresh_token) или статус.

## Архитектура

- **FastAPI**: Асинхронный веб-фреймворк.
- **SQLAlchemy**: ORM для PostgreSQL (async).
- **Redis**: Кэш, rate limiting, Arq queues.
- **Kafka**: События для других сервисов (budget, notifications).
- **Arq**: Фоновые задачи (email, Kafka, cron cleanup).
- **Middleware**: Обработка ошибок, логирование в JSON.
- **Модели**: Users (роли: USER=0, ADMIN=1, MODERATOR=2), Sessions.
- **Безопасность**: Bcrypt хэши, JWT RS256, GeoIP, User-Agent parsing.

## Интеграция с Другими Сервисами

- **Kafka Topics**: "budget.auth.events" для событий, "budget.users.active" для активных пользователей.
- **Другие Микросервисы**: Используйте JWKS для валидации токенов; слушайте события для синхронизации (e.g., notifications для email).

## Мониторинг и Логи

- Логи: JSON формат, уровень INFO по умолчанию.
- Prometheus: Метрики на /metrics.
- Healthchecks: В Docker Compose для зависимостей.

## Тестирование

- Установите тестовые зависимости: `pip install -r requirements-test.txt`.
- Запустите тесты: `pytest`.
- Покрытие: Фокус на unit (services, utils), integration (API, DB, Redis, Kafka mocks).

## Вклад в Развитие

- Ветка: service/authentification.
- Коммиты: Используйте Conventional Commits (feat:, fix:, chore:).
- Pull Requests: В dev, затем в prod.
- Issues: Открывайте в основном репозитории.

## Лицензия

MIT License. Copyright (c) 2025 SmartBudget Team.