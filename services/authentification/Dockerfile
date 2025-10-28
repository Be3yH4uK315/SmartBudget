FROM python:3.12-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /install /usr/local
ENV PATH=/usr/local/bin:$PATH

COPY ./app /app/app
COPY ./certs /app/certs
COPY alembic.ini /app/alembic.ini
COPY .env /app/.env

RUN mkdir /geoip
ENV GEOIP_DB_PATH=/geoip/GeoLite2-City.mmdb

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]