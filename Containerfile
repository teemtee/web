ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}

RUN mkdir /app
WORKDIR /app
COPY ./src /app/src
RUN pip install -r /app/src/requirements.txt

COPY /entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

