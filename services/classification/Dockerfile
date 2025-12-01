ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim as builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

RUN apt-get update && apt-get install -y netcat-openbsd postgresql-client libgomp1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
ENV PATH=/usr/local/bin:$PATH

COPY ./app /app/app

COPY alembic.ini /app/alembic.ini
COPY ./migrations /app/migrations

COPY run_consumers.py /app/run_consumers.py

RUN mkdir /models
ENV MODEL_PATH=/models

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8001", "--access-logfile", "-"]