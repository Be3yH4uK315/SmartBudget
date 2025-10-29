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
COPY alembic.ini /app/alembic.ini

RUN mkdir /geoip
ENV GEOIP_DB_PATH=/geoip/GeoLite2-City.mmdb

COPY ./geoip/GeoLite2-City.mmdb /geoip/GeoLite2-City.mmdb

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--forwarded-allow-ips", "*"]
