FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/api/

EXPOSE 8000

# UVICORN_WORKERS debe ser 1: el interruptor y el registro Prometheus viven
# en proceso. Con mas de un worker habria un interruptor por worker y el
# scrape caeria en uno u otro, invalidando toda la instrumentacion.
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-1} --log-level ${LOG_LEVEL:-warning} --no-access-log"]
