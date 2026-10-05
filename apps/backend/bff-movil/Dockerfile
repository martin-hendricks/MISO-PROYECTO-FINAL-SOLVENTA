FROM python:3.12.7-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv
COPY libs/solventa-seguridad ./libs/solventa-seguridad
COPY bff-movil/pyproject.toml ./bff-movil/
COPY bff-movil/app ./bff-movil/app
WORKDIR /srv/bff-movil

FROM base AS test
RUN pip install ".[test]"
COPY bff-movil/tests ./tests
CMD ["python", "-m", "pytest", "tests", "-m", "not integration and not contract", "--cov"]

FROM base AS runtime
RUN pip install . && useradd --uid 10001 --no-create-home app
USER app
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
