#!/bin/sh -eu

timeout=60

while true; do
    echo "[$(date)] Running readalert..."
    ./readalert.py
    echo "[$(date)] Done. Will run again in $timeout seconds."
    sleep "$timeout"
done
