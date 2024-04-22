#!/bin/sh

# Name of container to start
APP=$1

[ -z "$APP" ] && { error "No api to run passed to entrypoint script"; exit 1; }

if [ -z "$REDIS_URL" ] || [ -z "$TMP_DIR_PATH" ] || [ -z "$HOSTNAME" ]; then
  error "Missing one or more required environment variables"
  exit 1
fi

case $APP in
    uvicorn)
        COMMAND="uvicorn src.api:app --reload --host 0.0.0.0 --port 8000"
        ;;
    celery)
        COMMAND="celery --app=src.api.service worker --concurrency=1 --loglevel=INFO"
        ;;
    *)
        echo "Unknown app '$APP'"
        exit 1
        ;;
esac

$COMMAND &
PID=$!

wait $PID

