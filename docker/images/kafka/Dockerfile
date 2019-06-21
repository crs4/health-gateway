FROM blacktop/kafka:2.2

LABEL maintainer="Vittorio Meloni <vittorio.meloni@crs4.it>"

RUN apk update && \
    apk add nss python3

COPY resources/config/server.properties /opt/kafka/config/
COPY resources/scripts /

