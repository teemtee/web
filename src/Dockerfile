FROM python:3.10

RUN mkdir /app
WORKDIR /app
COPY ./ /app/src
RUN pip install -r /app/src/requirements.txt
CMD uvicorn src.api:app --reload