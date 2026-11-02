# Support IT — Helpdesk & Stock (version autonome)
# FastAPI + stockage JSON, sert aussi l'interface web déjà compilée (local_package/web).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=80

WORKDIR /app

# Mises à jour de sécurité du système dans la même couche que l'installation
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY local_package/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY local_package/app.py ./app.py
COPY local_package/web ./web
COPY local_package/data.json ./data.json

RUN mkdir -p uploads \
    && adduser --disabled-password --no-create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 80

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
