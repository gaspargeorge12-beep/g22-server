FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask flask-cors ifcopenshell

COPY main.py .

CMD ["python", "main.py"]
