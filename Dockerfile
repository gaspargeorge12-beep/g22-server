FROM python:3.11-slim
# v2

WORKDIR /app

COPY main.py .

RUN pip install --no-cache-dir flask flask-cors

CMD ["python", "main.py"]
