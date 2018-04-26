FROM alpine:3.7

RUN apk update && apk add gcc make ca-certificates openssl bash openjdk8-jre

RUN mkdir /scripts/

ADD *.sh /scripts/
ADD *.cnf /scripts/
ADD docker_entrypoint /docker-entrypoint
RUN chmod +x /docker-entrypoint

VOLUME /out/

ENTRYPOINT ["/docker-entrypoint"]
