# services/authentification/Dockerfile
FROM python:3.12-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim as final

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

COPY ./app /app/app
COPY alembic.ini /app/alembic.ini

RUN mkdir /geoip
ENV GEOIP_DB_PATH=/geoip/GeoLite2-City.mmdb

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]