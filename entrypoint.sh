#!/bin/sh

error() {
    echo "ERROR: $1" >&2
    exit 1
}

# Handle signals
trap 'kill -TERM $PID' TERM INT

# Name of container to start
APP=$1

[ -z "$APP" ] && error "No app to run passed to entrypoint script"

case $APP in
    uvicorn)
        COMMAND="uvicorn tmt_web.api:app --reload --host 0.0.0.0 --port 8000"
        ;;
    celery)
        COMMAND="celery --app=tmt_web.service worker --loglevel=INFO"
        ;;
    *)
        error "Unknown app '$APP'"
        ;;
esac

$COMMAND &
PID=$!

wait $PID
