FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY protocol /app/protocol
COPY server /app/server
RUN pip install --no-cache-dir /app/protocol "/app/server[deploy]"

WORKDIR /app/server
RUN DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn learnharness_server.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
