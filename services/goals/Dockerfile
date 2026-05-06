ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build/services/goals

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY services/goals/requirements.txt .
COPY shared/python /build/shared/python

RUN pip wheel --no-cache-dir --no-deps --wheel-dir /tmp/wheels -r requirements.txt

FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system appgroup && adduser --system --group appuser

COPY --from=builder /tmp/wheels /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/* && rm -rf /tmp/wheels

COPY --chown=appuser:appgroup services/goals/app /app/app

COPY --chown=appuser:appgroup services/goals/alembic.ini /app/alembic.ini
COPY --chown=appuser:appgroup services/goals/alembic /app/alembic

USER appuser

ENV HOME=/tmp
ENV PYTHONPATH=/app
ENV PATH="/home/appuser/.local/bin:$PATH"

CMD ["gunicorn", "app.main:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
