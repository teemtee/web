#!/bin/sh

error() {
    echo "ERROR: $1" >&2
    exit 1
}

# Handle signals
trap 'kill -TERM $PID' TERM INT

uvicorn tmt_web.api:app --reload --host 0.0.0.0 --port 8000 &

PID=$!

wait $PID
