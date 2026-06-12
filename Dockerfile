FROM continuumio/miniconda3:23.10.0-1

WORKDIR /app

RUN conda install -c conda-forge pythonocc-core=7.7.2 python=3.11 -y --quiet \
    && conda clean -afy

RUN pip install --no-cache-dir flask flask-cors gunicorn

COPY main.py .

CMD gunicorn main:app --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 180
