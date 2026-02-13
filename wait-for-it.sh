#!/bin/bash
# wait-for-it.sh - Wait for service availability
# Usage: ./wait-for-it.sh host:port [-t timeout] [-- command args]

set -e

TIMEOUT=60
QUIET=0
HOST=""
PORT=""
CMD=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        *:* )
            HOST=$(echo $1 | cut -d: -f1)
            PORT=$(echo $1 | cut -d: -f2)
            shift
            ;;
        -t)
            TIMEOUT="$2"
            shift 2
            ;;
        -q)
            QUIET=1
            shift
            ;;
        --)
            shift
            CMD="$@"
            break
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

# Validate host and port
if [ -z "$HOST" ] || [ -z "$PORT" ]; then
    echo "Error: Host and port must be specified (e.g., mysql:3306)"
    exit 1
fi

# Wait for service
ELAPSED=0
until nc -z "$HOST" "$PORT" 2>/dev/null; do
    if [ $ELAPSED -ge $TIMEOUT ]; then
        echo "Timeout waiting for $HOST:$PORT after ${TIMEOUT}s"
        exit 1
    fi

    if [ $QUIET -ne 1 ]; then
        echo "Waiting for $HOST:$PORT... ($ELAPSED/$TIMEOUT)"
    fi

    sleep 1
    ELAPSED=$((ELAPSED + 1))
done

if [ $QUIET -ne 1 ]; then
    echo "$HOST:$PORT is available after ${ELAPSED}s"
fi

# Execute command if provided
if [ -n "$CMD" ]; then
    exec $CMD
fi
