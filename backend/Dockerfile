FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libglib2.0-0 libgobject-2.0-0 libffi-dev libcairo2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini ./
COPY alembic_migrations ./alembic_migrations
COPY app ./app
COPY scripts ./scripts

RUN chmod +x ./scripts/entrypoint.sh

EXPOSE 8000

CMD ["./scripts/entrypoint.sh"]
