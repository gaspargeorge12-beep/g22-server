FROM cadquery/cadquery:latest

WORKDIR /app

RUN /opt/conda/envs/cq/bin/pip install flask flask-cors gunicorn

COPY main.py .

CMD ["/opt/conda/envs/cq/bin/gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "120", "--workers", "1", "main:app"]
