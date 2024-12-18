ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}

RUN mkdir /app
WORKDIR /app
COPY README.md LICENSE pyproject.toml ./
COPY src/tmt_web/ ./tmt_web/

RUN SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0.dev0 pip install .

COPY /entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

LABEL org.opencontainers.image.title="tmt-web"
LABEL org.opencontainers.image.description="Web API for checking tmt tests, plans and stories"
LABEL org.opencontainers.image.source="https://github.com/teemtee/tmt-web"

ENTRYPOINT ["/entrypoint.sh"]
