# Сервис аутентификации (Auth Service)

Отвечает за регистрацию пользователей, вход в систему, выдачу JWT-токенов, обновление токенов и JWKS-эндпоинт.

## Технологии
- Python 3.12
- FastAPI
- PostgreSQL
- Redis

## Запуск локально
```bash
uvicorn app.main:app --reload
