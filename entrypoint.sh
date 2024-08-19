#!/bin/sh

# Name of container to start
APP=$1

[ -z "$APP" ] && { error "No api to run passed to entrypoint script"; exit 1; }

case $APP in
    uvicorn)
        COMMAND="uvicorn tmt_web.api:app --reload --host 0.0.0.0 --port 8000"
        ;;
    celery)
        COMMAND="celery --app=tmt_web.api.service worker --loglevel=INFO"
        ;;
    *)
        echo "Unknown app '$APP'"
        exit 1
        ;;
esac

$COMMAND &
PID=$!

wait $PID
