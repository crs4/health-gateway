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

function usage {
    echo "Creates certificates for CAs and for services. By default it creates web and kafka certs for consentmanager hgwfrontend hgwbackend. If you need other services specify them"
    echo "usage: ${0} [-s] [-h] [list of additional services]"
    echo " -o       specify output dir. If not present it will use the current dir"
    echo " -h       print this message"
}

OUTPUT_DIR=""

if [ $# -ge 1 ]; then
    case "$1" in
        -h)
            usage
            exit 1
            ;;
        -o)
            if [ "$#" = 1 ]; then
                echo ERROR: Missing param for -o option
                exit 1
            fi
            OUTPUT_DIR=$2
            ;;
    esac
fi

./generate_all.sh destinationmockup i2b2-destination source-endpoint-mockup integration-rest-destination

mv -r web ca/

./generate_ts_cns_saml_certs.sh

# Creates the hgwbackend client cert for the source_endpoint_mockup
./generate_web_certs.sh hgwbackend_client ca/web/certs/hgwbackend/source_endpoint_mockup_client true
./generate_web_certs.sh tscns ca/web/certs/tscns/idp_server true

if [ "$OUTPUT_DIR" != "" ]; then
    mv ca/* $OUTPUT_DIR
fi