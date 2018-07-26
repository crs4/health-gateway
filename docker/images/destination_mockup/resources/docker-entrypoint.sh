#!/bin/bash
# Copyright (c) 2017-2018 CRS4
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# It checks if there are files in the development directory (1 because ls -l print at least the number of files)
if [ `ls -l ${DEV_DJANGO_DIR} | wc -l` == 1 ]; then
    echo "USING PROD DIR"
    cd ${DJANGO_DIR}
    export BASE_SERVICE_DIR=${DEV_DJANGO_DIR}
else
    echo "USING DEV DIR"
    cd ${DEV_DJANGO_DIR}
    export BASE_SERVICE_DIR=${DEV_DJANGO_DIR}
fi

INITIALIZED="/container/initialized"

if [ ! -e "$INITIALIZED" ]; then
	python3 manage.py migrate
	touch ${INITIALIZED}

fi

CONSUMER_TYPE=$1
if [ -z ${CONSUMER_TYPE}  ] || [ ${CONSUMER_TYPE} == 'kafka' ]; then
    CONSUMER=kafka_consumer
else
    CONSUMER=rest_consumer
fi

echo "Starting $CONSUMER"
python3 manage.py ${CONSUMER} &
if [ "$?" == "0" ]; then
    echo "Started"
fi

envsubst '${HTTP_PORT} ${BASE_SERVICE_DIR}' < /etc/nginx/conf.d/nginx_https.template > /etc/nginx/conf.d/https.conf
nginx
gunicorn_start.sh
