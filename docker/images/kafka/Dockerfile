FROM alpine:3.6

LABEL maintainer="Vittorio Meloni <vittorio.meloni@crs4.it>"

ARG KAFKA_VERSION_ARG=0.11.0.2
ARG SCALA_VERSION_ARG=2.12

ENV KAFKA_VERSION=${KAFKA_VERSION_ARG}
ENV SCALA_VERSION=${SCALA_VERSION_ARG}

LABEL name="kafka" version=${KAFKA_VERSION}

RUN apk add --no-cache openjdk8-jre docker bash coreutils su-exec
RUN apk add --no-cache -t .build-deps curl ca-certificates jq \
  && mkdir -p /opt \
	&& curl -sSL "https://archive.apache.org/dist/kafka/${KAFKA_VERSION}/kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz" \
		| tar -xzf - -C /opt \
	&& mv /opt/kafka_${SCALA_VERSION}-${KAFKA_VERSION} /opt/kafka \
  && adduser -DH -s /sbin/nologin kafka \
  && chown -R kafka: /opt/kafka \
  && rm -rf /tmp/* \
  && apk del --purge .build-deps

ENV PATH /sbin:/opt/kafka/bin/:$PATH

WORKDIR /opt/kafka

VOLUME ["/tmp/kafka-logs"]

EXPOSE 9092 9093 2181

COPY resources/config/log4j.properties /opt/kafka/config/
COPY resources/config/server.properties /opt/kafka/config/
COPY resources/config/zookeeper.properties /opt/kafka/config/
COPY resources/kafka-entrypoint.sh /kafka-entrypoint.sh
COPY resources/scripts /

VOLUME /container/certs

ENTRYPOINT ["/kafka-entrypoint.sh"]
CMD ["kafka-server-start.sh", "config/server.properties"]

# HEALTHCHECK --interval=5s --timeout=2s --retries=5 CMD bin/health.sh
