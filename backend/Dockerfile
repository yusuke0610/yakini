FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini ./
COPY alembic_migrations ./alembic_migrations
COPY app ./app
COPY scripts ./scripts

RUN chmod +x ./scripts/entrypoint.sh

EXPOSE 8000

CMD ["./scripts/entrypoint.sh"]
