FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask flask-cors pythonocc-core==7.7.0

COPY main.py .

CMD ["python", "main.py"]
