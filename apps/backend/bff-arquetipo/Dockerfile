FROM python:3.12.7-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv
COPY libs/solventa-seguridad ./libs/solventa-seguridad
COPY bff-arquetipo/pyproject.toml ./bff-arquetipo/
COPY bff-arquetipo/app ./bff-arquetipo/app
WORKDIR /srv/bff-arquetipo

FROM base AS test
RUN pip install ".[test]"
COPY bff-arquetipo/tests ./tests
CMD ["python", "-m", "pytest", "tests", "-m", "not integration and not contract", "--cov"]

FROM base AS runtime
RUN pip install . && useradd --uid 10001 --no-create-home app
USER app
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
