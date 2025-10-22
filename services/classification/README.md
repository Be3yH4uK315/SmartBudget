# Сервис классификации (Classification Service)

Классифицирует транзакции пользователей по категориям, используя ML-модель или набор правил.

## Технологии
- Python 3.12
- FastAPI
- scikit-learn / TensorFlow
- Redis (кэширование)

## Запуск локально
```bash
uvicorn app.main:app --reload