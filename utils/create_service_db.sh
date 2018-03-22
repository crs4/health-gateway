#!/usr/bin/env bash
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




if [ -z "$1" ]; then
    LOAD_DEV_DATA="true"
else
    LOAD_DEV_DATA="$1"
    if [ ${LOAD_DEV_DATA} != "true" ] && [ ${LOAD_DEV_DATA} != "false" ]; then
        echo "$LOAD_DEV_DATA"
        echo "LOAD_DEV_DATA should be true or false"
        exit 1;
    fi
fi

parent_dir="$(dirname -- "$(realpath -- "$0")")"
export PYTHONPATH=${parent_dir}/../hgw_common/
for d in consent_manager destination_mockup hgw_backend hgw_frontend examples/source_endpoint; do
    echo "Recreating db for service ${d}"
    echo $(pwd)
    cd ../${d}
    echo $(pwd)
    rm -f *.sqlite3
    python3 manage.py migrate
    if [ -f ${d}/fixtures/initial_data.json ]; then
        python3 manage.py loaddata initial_data
    fi
    if [ ${LOAD_DEV_DATA} = "true" ] &&  [ -f ${d}/fixtures/initial_data.json ]; then
        python3 manage.py loaddata development_data
    fi
done