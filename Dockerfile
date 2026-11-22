FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements-deploy.txt ./
RUN pip install --no-cache-dir -r requirements-deploy.txt \
    && groupadd -r adaptlearn \
    && useradd -r --create-home -g adaptlearn -s /usr/sbin/nologin adaptlearn \
    && install -d -o adaptlearn -g adaptlearn /app/instance

COPY *.py ./
COPY templates/ templates/
COPY static/ static/
COPY scripts/ scripts/

USER adaptlearn
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--preload", "--timeout", "90", "app:create_app()"]
