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


#!/bin/bash

FIRST_START_DONE="/tmp/slapd-first-start-done"

if [ ! -e "$FIRST_START_DONE" ]; then
	python3 manage.py migrate
	touch ${FIRST_START_DONE}

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

if [[ -z ${DEVELOPMENT} ]]; then
    #chown gunicorn:gunicorn /var/lib/*.sqlite3
    envsubst '${HTTP_PORT}' < /etc/nginx/conf.d/nginx_https.template > /etc/nginx/conf.d/https.conf
    nginx
    gunicorn_start.sh
else
    expect -f launch_python_development.exp
fi