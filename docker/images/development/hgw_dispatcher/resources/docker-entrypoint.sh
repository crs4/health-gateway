#!/usr/bin/env bash

python3 ${CONTAINER_DIR}/service/dispatcher.py
STATUS=$?
while [ ${STATUS} == 2 ]; do
    echo "Not ready. Sleeping 5 seconds"
    sleep 5
    python3 ${CONTAINER_DIR}/service/dispatcher.py
    STATUS=$?
    echo "STATUS: $STATUS"
done