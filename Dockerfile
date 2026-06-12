FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    flask \
    flask-cors \
    gunicorn \
    "https://github.com/tpaviot/pythonocc-core/releases/download/7.7.2/pythonocc_core-7.7.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"

COPY main.py .

CMD gunicorn main:app --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 120
