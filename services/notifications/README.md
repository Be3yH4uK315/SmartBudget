# Сервис уведомлений (Notification Service)

Отвечает за отправку email, push и SMS уведомлений пользователям.  
Может использовать очереди и фоновые задачи (Celery / RabbitMQ).

## Технологии
- Python 3.12
- FastAPI
- Celery + Redis
- SMTP / Firebase / Twilio

## Запуск локально
```bash
uvicorn app.main:app --reload