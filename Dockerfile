FROM cadquery/cadquery:latest

WORKDIR /app

RUN pip install --no-cache-dir flask flask-cors

COPY main.py .

CMD ["python", "main.py"]
