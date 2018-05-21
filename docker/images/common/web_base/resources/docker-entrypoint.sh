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


INITIALIZED="/container/initialized"

if [ ! -e "$INITIALIZED" ]; then
	python3 manage.py migrate
    python3 manage.py loaddata initial_data
    FIXTURES_DIR=/container/fixtures
    TEST_FIXTURES_DIR=/container/test_fixtures
    for fixture_dir in $FIXTURES_DIR $TEST_FIXTURES_DIR; do
        if [ -d $fixture_dir ]; then
            for fixture in `ls $fixture_dir/*.json`; do
                python3 manage.py loaddata $fixture
            done
        fi
    done
	touch ${INITIALIZED}
fi

envsubst '${HTTP_PORT}' < /etc/nginx/conf.d/nginx_https.template > /etc/nginx/conf.d/https.conf
nginx
gunicorn_start.sh
