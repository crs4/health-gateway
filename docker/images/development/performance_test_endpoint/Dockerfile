# Base image for Django services
FROM crs4/hgw_base
MAINTAINER Vittorio Meloni <vittorio.meloni@crs4.it>

ENV CONTAINER_DIR=/container

RUN apk update && apk add gcc make python3 python3-dev py3-pip openssl-dev libc-dev bash
RUN pip3 install kafka-python pycryptodomex docker

ADD resources/wait-for-it.sh /custom_entrypoint/
RUN chmod +x /custom_entrypoint/wait-for-it.sh

WORKDIR $CONTAINER_DIR/service

ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

VOLUME $CONTAINER_DIR/certs
VOLUME $CONTAINER_DIR/service
