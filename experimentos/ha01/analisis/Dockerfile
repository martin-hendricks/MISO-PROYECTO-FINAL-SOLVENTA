# Imagen SOLO para el analisis. Deliberadamente separada de la de la API:
# meter matplotlib en el contenedor que se mide cambiaria su huella de memoria
# y su tiempo de arranque, que son parte del montaje bajo estudio.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg
WORKDIR /work

RUN pip install --no-cache-dir matplotlib==3.10.0
