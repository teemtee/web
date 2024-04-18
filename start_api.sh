#!/usr/bin/env bash
# For local dev purposes
docker run --rm --name some-redis -p 6379:6379 redis:latest &
celery --app=src.api.service worker --concurrency=1 --loglevel=INFO &
uvicorn src.api:app --reload && fg
