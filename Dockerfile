FROM cadquery/cadquery:latest

WORKDIR /app

RUN /opt/conda/envs/cq/bin/pip install flask flask-cors

COPY main.py .

CMD ["/opt/conda/envs/cq/bin/python", "main.py"]
