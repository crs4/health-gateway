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


FROM crs4/hgw_base
MAINTAINER Vittorio Meloni <vittorio.meloni@crs4.it>

ENV CERTS_DIR=/container/certs

RUN apk update && apk add python3 python3-dev py3-pip
RUN pip3 install kafka-python requests requests-oauthlib oauthlib PyYAML

ADD resources/wait-for-it.sh /custom_entrypoint/
ADD resources/docker-entrypoint.sh /custom_entrypoint/
ADD service /container/service
RUN chmod +x /custom_entrypoint/wait-for-it.sh
RUN chmod +x /custom_entrypoint/docker-entrypoint.sh

ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

VOLUME ${CERTS_DIR}

WORKDIR ${CONTAINER_DIR}