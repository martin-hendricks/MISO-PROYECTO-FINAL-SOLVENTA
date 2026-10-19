FROM python:3.12.7-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv
COPY bff-arquetipo/pyproject.toml ./bff-arquetipo/
COPY bff-arquetipo/app ./bff-arquetipo/app
COPY bff-arquetipo/requirements.lock ./bff-arquetipo/
WORKDIR /srv/bff-arquetipo

FROM base AS test
RUN pip install -c requirements.lock ".[test]"
COPY bff-arquetipo/tests ./tests
CMD ["python", "-m", "pytest", "tests", "-m", "not integration and not contract", "--allow-hosts=127.0.0.1,::1", "--cov"]

FROM base AS runtime
RUN pip install -c requirements.lock . && useradd --uid 1000 --no-create-home app
USER app
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
