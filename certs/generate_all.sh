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



./generate_root_certs.sh
./generate_intermediate_certs.sh web
./generate_intermediate_certs.sh kafka
for service in consentmanager destinationmockup hgwfrontend hgwbackend i2b2-destination source-endpoint-mockup; do
    ./generate_web_certs.sh ${service}
done

./generate_kafka_server_certificates.sh
for service in destinationmockup hgwbackend hgwdispatcher hgwfrontend i2b2-destination \
    integration-rest-destination source-endpoint-mockup; do
    ./generate_kafka_client_certificates.sh ${service}
done

# Creates the hgwbackend client cert for the source_endpoint_mockup
./generate_web_certs.sh hgwbackend_client ca/web/certs/hgwbackend/source_endpoint_mockup_client true