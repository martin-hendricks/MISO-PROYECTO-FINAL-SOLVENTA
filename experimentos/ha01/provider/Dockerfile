FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY provider.py .

EXPOSE 9000

# Mas workers que la API a proposito: el doble NO puede ser el cuello de
# botella. Si lo fuera, el experimento mediria el doble en vez del diseno.
CMD ["sh", "-c", "uvicorn provider:app --host 0.0.0.0 --port 9000 --workers ${PROVIDER_WORKERS:-1} --log-level warning --no-access-log"]
