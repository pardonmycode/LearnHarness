FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY protocol /app/protocol
COPY server /app/server
RUN pip install --no-cache-dir /app/protocol /app/server

WORKDIR /app/server
RUN DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput

EXPOSE 8000
# daphne serves HTTP and the tutor WebSocket (/api/v1/sessions/<id>/stream).
CMD ["sh", "-c", "python manage.py migrate --noinput && daphne -b 0.0.0.0 -p 8000 learnharness_server.asgi:application"]
