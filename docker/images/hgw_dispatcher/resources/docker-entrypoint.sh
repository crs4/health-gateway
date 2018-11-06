#!/usr/bin/env bash

# It checks if there are files in the development directory (1 because ls -l print at least the number of files)
if [ `ls -l /container/devservice | wc -l` == 1 ]; then
    echo "USING PROD DIR"
    export BASE_SERVICE_DIR=/container/service
else
    echo "USING DEV DIR"
    export BASE_SERVICE_DIR=/container/devservice
fi
cd ${BASE_SERVICE_DIR}

python3 ${BASE_SERVICE_DIR}/dispatcher.py
STATUS=$?
while [ ${STATUS} == 2 ]; do
    echo "Not ready. Sleeping 5 seconds"
    sleep 5
    python3 ${BASE_SERVICE_DIR}/dispatcher.py
    STATUS=$?
    echo "STATUS: $STATUS"
done