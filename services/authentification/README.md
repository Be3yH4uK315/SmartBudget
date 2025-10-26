# Auth Service

Центральный сервис аутентификации и авторизации для системы "Умный бюджет". Обеспечивает регистрацию с email-верификацией, логин/логаут, управление сессиями (с device/location), восстановление/смену пароля, валидацию JWT через JWKS. Интегрируется с Kafka для событий, PostgreSQL для данных, Redis для токенов/rate limiting, Celery для async задач (email, cleanup).

## Технологии
- Backend: Python 3.12, FastAPI
- DB: PostgreSQL (async с SQLAlchemy)
- Messaging: Kafka (aiokafka)
- Cache: Redis
- Tasks: Celery
- Auth: PyJWT, bcrypt
- Parsing: geoip2 (MaxMind GeoLite2), user-agents
- Email: aiosmtplib
- Migrations: Alembic
- Monitoring: Prometheus
- Limiting: fastapi-limiter

## Установка и запуск локально
1. Клонируйте репозиторий: `git clone https://github.com/4y8a4ek/SmartBudget.git`
2. Перейдите в `services/authentification`
3. Создайте виртуальное окружение: `python -m venv .venv && source .venv/bin/activate`
4. Установите зависимости: `pip install -r requirements.txt`
5. Скачайте GeoLite2-City.mmdb с https://dev.maxmind.com/geoip/geolite2-free-geolocation-data и поместите в удобный путь.
6. Создайте .env на основе .env.example, заполните значения (DATABASE_URL, etc.).
7. Запустите инфраструктуру: `docker compose -f ../../../infra/compose/docker-compose.dev.yml up -d` (из корня репозитория)
8. Создайте Kafka топики: `docker exec -it auth_kafka_dev kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic budget.auth.events` (и для users.active)
9. Инициализируйте/примените миграции: `alembic revision --autogenerate -m "changes"` и `alembic upgrade head`
10. Запустите API: `uvicorn app.main:app --reload`
11. Запустите Celery worker: `celery -A app.tasks.app worker --loglevel=INFO`
12. Запустите Celery beat для schedules: `celery -A app.tasks.app beat --loglevel=INFO`

## Docker
- Build: `docker build -t auth-service .`
- Run: `docker run -p 8000:8000 --env-file .env -v /path/to/geoip:/geoip auth-service`
- В docker-compose.prod.yml добавьте сервис auth с depends_on: postgres, redis, kafka.

## Тестирование
- Unit/API: `pytest`
- Coverage: `pytest --cov=app`

## Расширения
- 2FA, social login

## Контакты
Разработчик: Костерин Дмитрий