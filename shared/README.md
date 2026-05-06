# Shared modules

Общие модули для backend-сервисов SmartBudget.

## Python package

Пакет `smartbudget_shared` расположен в `shared/python` и подключается в сервисах как editable dependency:

```txt
-e ../../shared/python
```

Текущая структура:

```txt
shared/python/
├── setup.py
├── requirements-shared.txt
└── smartbudget_shared/
    ├── app/
    │   └── lifespan.py
    ├── config/
    │   └── __init__.py
    └── health/
        ├── checks.py
        └── service.py
```

Использование в сервисах:

- `smartbudget_shared.config` - базовые `BaseSettings` классы для `DB`, `ARQ`, `APP`, `Redis`, `Kafka`;
- `smartbudget_shared.health` - переиспользуемые health checks для DB, Redis и ARQ;
- `smartbudget_shared.app` - вспомогательные lifecycle-утилиты для FastAPI-приложений.

## Docker build

Python-сервисы собираются с context корня монорепозитория, чтобы Dockerfile мог скопировать и сервис, и `shared/python`.

