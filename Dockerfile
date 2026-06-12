FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask flask-cors gunicorn

COPY main.py .

CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:8080", "--workers", "1"]
