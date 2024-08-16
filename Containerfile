ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}

RUN mkdir /app
WORKDIR /app
COPY README.md LICENSE pyproject.toml src/ ./

RUN SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0.dev0 pip install .

COPY /entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

