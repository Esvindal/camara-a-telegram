# syntax=docker/dockerfile:1
FROM python:3.12-slim AS build
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 1001 app && useradd -u 1001 -g app -m app
WORKDIR /app
COPY --from=build /install /usr/local
USER app
VOLUME ["/app/datos"]
ENV DB_PATH=/app/datos/eventos.db \
    PYTHONUNBUFFERED=1
ENTRYPOINT ["camara-a-telegram"]
CMD ["run", "--fuente", "simulator", "--dry-run"]
