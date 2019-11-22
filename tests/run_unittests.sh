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



if [ ! -z $1 ]; then
    PYTHON_VERSION="$1"
    PYTHON=python2
else
    PYTHON_VERSION="3"
    PYTHON=python3
fi

echo "Using $PYTHON" 

set -e

SCRIPT_PATH=$(readlink -f "$0")
DIR=$(dirname $SCRIPT_PATH)
echo $DIR
export PYTHONPATH=${DIR}/../hgw_common

for module in consent_manager hgw_frontend hgw_backend; do
    echo $'\n*********************'
    echo "Testing $module"
    cd $DIR/../${module}
    ${PYTHON} manage.py test test/ || echo "At least one test FAILED"
done

cd $DIR/../hgw_common/hgw_common
echo $'\n*********************'
echo "Testing hgw_common"
${PYTHON} manage.py test test/

# if [ "${PYTHON_VERSION}" ==  "3" ]; then
#     cd $DIR/../hgw_dispatcher/
#     echo $'\n*********************'
#     echo "Testing hgw_dispatcher"
#     python3 -m unittest test
# fi
