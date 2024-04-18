FROM python:3.10

RUN mkdir /app
WORKDIR /app

RUN pip install celery

COPY ./src /app/src
RUN pip install -r /app/src/requirements.txt
CMD celery --app=src.api.service worker --concurrency=1 --loglevel=INFO