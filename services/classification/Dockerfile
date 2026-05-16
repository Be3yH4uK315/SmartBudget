ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build/services/classification

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY services/classification/requirements.txt .
COPY shared/python /build/shared/python
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /tmp/wheels -r requirements.txt

FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    libgomp1 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system appgroup && adduser --system --group appuser

RUN mkdir -p /app/datasets /models \
    && chown -R appuser:appgroup /app/datasets /models

COPY --from=builder /tmp/wheels /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/* && rm -rf /tmp/wheels

COPY services/classification/app /app/app
COPY services/classification/alembic.ini /app/alembic.ini
COPY services/classification/alembic /app/alembic
COPY services/classification/init_rules.py /app/init_rules.py
RUN chown -R appuser:appgroup /app

USER appuser

ENV HOME=/tmp
ENV PYTHONPATH=/app
ENV ML__MODEL_PATH=/models
ENV ML__DATASET_PATH=/app/datasets
ENV PATH="/home/appuser/.local/bin:$PATH"

CMD ["gunicorn", "app.main:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8001"]
