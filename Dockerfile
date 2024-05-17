FROM python:3.10

RUN mkdir /app
WORKDIR /app
COPY ./src /app/src
RUN pip install -r /app/src/requirements.txt

COPY /entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

