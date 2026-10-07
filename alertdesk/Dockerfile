FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY alertdesk ./alertdesk
RUN pip install --no-cache-dir . \
    && groupadd --system app \
    && useradd --system --gid app --create-home app \
    && mkdir -p /app/data \
    && chown app:app /app/data

COPY config ./config

USER app
EXPOSE 8000

CMD ["uvicorn", "alertdesk.app:app", "--host", "0.0.0.0", "--port", "8000"]
