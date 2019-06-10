# Base image for Django services
FROM nginx:1.16.0-alpine
LABEL maintainer="Vittorio Meloni <vittorio.meloni@crs4.it>"

# # https://bugs.alpinelinux.org/issues/9110 is fixed since xmlsec 1.2.25-r4.
# RUN echo "@edge http://nl.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories
# RUN echo "@edgecommunity http://nl.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories

RUN apk update && apk add --no-cache gcc make python3 python3-dev py3-pip \
	ca-certificates libressl-dev bash xmlsec xmlsec-dev libc-dev libxml2-dev \
	libffi-dev python2-dev expect \
    git postgresql-libs postgresql-dev

ENV CONTAINER_DIR=/container/
ENV CA_DIR=/cacerts/
ENV DJANGO_DIR=/container/service
ENV CERT_DIR=/container/certs
ENV DEV_DJANGO_DIR=/container/devservice
ARG DJANGO_VERSION=1.11.0
ARG HTTP_PORT=80

RUN pip3 install Django==${DJANGO_VERSION} \
    gunicorn==19.7.1 \
	mock==2.0.0 \
    djangorestframework==3.8.2 \
	django-oauth-toolkit==0.12.0 \
	django-cors-middleware==1.3.1 \
	requests==2.18.4 \
	requests_oauthlib==0.8.0 \
	kafka_python==1.3.5 \
	pycryptodomex==3.4.7 \
	coreapi==2.3.3 \
	drf_yasg \
	PyYAML==3.12 \
	coverage \
	psycopg2 \
	urllib3==1.25.3

RUN git clone -b develop https://github.com/crs4/djangosaml2.git && cd djangosaml2 && python3 setup.py install

RUN addgroup -S gunicorn && adduser -D -S -s /sbin/nologin -G gunicorn gunicorn

RUN ln -sf /usr/bin/python3 /usr/bin/python

RUN mkdir ${CONTAINER_DIR}
RUN mkdir ${CA_DIR}
RUN mkdir /custom_entrypoint/
RUN mkdir ${DJANGO_DIR} && chown -R gunicorn:gunicorn ${DJANGO_DIR}
RUN mkdir ${CERT_DIR}
RUN mkdir ${DEV_DJANGO_DIR}

RUN echo hgwpwd > /etc/nginx/passw
RUN chown nginx:nginx /etc/nginx/passw && chmod 600 /etc/nginx/passw

ADD resources/nginx.conf /etc/nginx/nginx.conf
ADD resources/custom-docker-entrypoint.sh /custom_entrypoint/docker-entrypoint.sh
ADD resources/docker-entrypoint.sh /
ADD resources/wait-for-it.sh /custom_entrypoint/
ADD resources/nginx_https.template /etc/nginx/conf.d/nginx_https.template
ADD resources/gunicorn_start.sh /usr/local/bin

RUN chmod +x /docker-entrypoint.sh
RUN chmod +x /custom_entrypoint/docker-entrypoint.sh
RUN chmod +x /custom_entrypoint/wait-for-it.sh

VOLUME "${CA_DIR}/"
VOLUME "${CONTAINER_DIR}"
VOLUME "${DEV_DJANGO_DIR}/"
VOLUME "${CONTAINER_DIR}/web_certs/"
VOLUME "${CONTAINER_DIR}/certs/"

ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

WORKDIR ${CONTAINER_DIR}

STOPSIGNAL SIGTERM

ENTRYPOINT ["/docker-entrypoint.sh"]

