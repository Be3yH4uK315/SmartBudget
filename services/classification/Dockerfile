ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
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

RUN mkdir -p /app/datasets /models /app/ml_models \
    && chown -R appuser:appgroup /app/datasets /models /app/ml_models

COPY --from=builder /tmp/wheels /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/* && rm -rf /tmp/wheels

COPY . /app
RUN chown -R appuser:appgroup /app

USER appuser

ENV PYTHONPATH=/app
ENV MODEL_PATH=/models
ENV PATH="/home/appuser/.local/bin:$PATH"

CMD ["gunicorn", "app.main:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8001"]
