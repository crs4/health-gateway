# Base image for Django services
FROM crs4/hgw_base
MAINTAINER Vittorio Meloni <vittorio.meloni@crs4.it>

ENV NGINX_VERSION 1.12.1
ENV GPG_KEYS=B0F4253373F8F6F510D42178520A9993A1C052F8
ENV NGINX_CONFIG="\
		--prefix=/etc/nginx \
		--sbin-path=/usr/sbin/nginx \
		--modules-path=/usr/lib/nginx/modules \
		--conf-path=/etc/nginx/nginx.conf \
		--error-log-path=/var/log/nginx/error.log \
		--http-log-path=/var/log/nginx/access.log \
		--pid-path=/var/run/nginx.pid \
		--lock-path=/var/run/nginx.lock \
		--http-client-body-temp-path=/var/cache/nginx/client_temp \
		--http-proxy-temp-path=/var/cache/nginx/proxy_temp \
		--http-fastcgi-temp-path=/var/cache/nginx/fastcgi_temp \
		--http-uwsgi-temp-path=/var/cache/nginx/uwsgi_temp \
		--http-scgi-temp-path=/var/cache/nginx/scgi_temp \
		--user=nginx \
		--group=nginx \
		--with-http_ssl_module \
		--with-http_realip_module \
		--with-http_addition_module \
		--with-http_sub_module \
		--with-http_dav_module \
		--with-http_flv_module \
		--with-http_mp4_module \
		--with-http_gunzip_module \
		--with-http_gzip_static_module \
		--with-http_random_index_module \
		--with-http_secure_link_module \
		--with-http_stub_status_module \
		--with-http_auth_request_module \
		--with-http_xslt_module=dynamic \
		--with-http_image_filter_module=dynamic \
		--with-http_geoip_module=dynamic \
		--with-threads \
		--with-stream \
		--with-stream_ssl_module \
		--with-stream_ssl_preread_module \
		--with-stream_realip_module \
		--with-stream_geoip_module=dynamic \
		--with-http_slice_module \
		--with-mail \
		--with-mail_ssl_module \
		--with-compat \
		--with-file-aio \
		--with-http_v2_module"

RUN addgroup -S nginx
RUN adduser -D -S -h /var/cache/nginx -s /sbin/nologin -G nginx nginx
RUN apk add --no-cache --virtual .build-deps \
		libc-dev \
		pcre-dev \
		zlib-dev \
		linux-headers \
		curl \
		gnupg \
		libxslt-dev \
		gd-dev \
		geoip-dev
RUN curl -fSL http://nginx.org/download/nginx-$NGINX_VERSION.tar.gz -o nginx.tar.gz
RUN curl -fSL http://nginx.org/download/nginx-$NGINX_VERSION.tar.gz.asc  -o nginx.tar.gz.asc
RUN found=''; \
	for server in \
		ha.pool.sks-keyservers.net \
		hkp://keyserver.ubuntu.com:80 \
		hkp://p80.pool.sks-keyservers.net:80 \
		pgp.mit.edu \
	; do \
		echo "Fetching GPG key $GPG_KEYS from $server"; \
		gpg --keyserver "$server" --keyserver-options timeout=10 --recv-keys "$GPG_KEYS" && found=yes && break; \
	done; \
	test -z "$found" && echo >&2 "error: failed to fetch GPG key $GPG_KEYS" && exit 1; \
	gpg --batch --verify nginx.tar.gz.asc nginx.tar.gz
RUN rm -r "$(mktemp -d)" nginx.tar.gz.asc
RUN mkdir -p /usr/src
RUN tar -zxC /usr/src -f nginx.tar.gz
RUN rm nginx.tar.gz
WORKDIR /usr/src/nginx-$NGINX_VERSION
RUN ./configure $NGINX_CONFIG --with-debug \
	&& make -j$(getconf _NPROCESSORS_ONLN) \
	&& mv objs/nginx objs/nginx-debug \
	&& mv objs/ngx_http_xslt_filter_module.so objs/ngx_http_xslt_filter_module-debug.so \
	&& mv objs/ngx_http_image_filter_module.so objs/ngx_http_image_filter_module-debug.so \
	&& mv objs/ngx_http_geoip_module.so objs/ngx_http_geoip_module-debug.so \
	&& mv objs/ngx_stream_geoip_module.so objs/ngx_stream_geoip_module-debug.so \
	&& ./configure $NGINX_CONFIG \
	&& make -j$(getconf _NPROCESSORS_ONLN) \
	&& make install \
	&& rm -rf /etc/nginx/html/ \
	&& mkdir /etc/nginx/conf.d/ \
	&& mkdir -p /usr/share/nginx/html/ \
	&& install -m644 html/index.html /usr/share/nginx/html/ \
	&& install -m644 html/50x.html /usr/share/nginx/html/ \
	&& install -m755 objs/nginx-debug /usr/sbin/nginx-debug \
	&& install -m755 objs/ngx_http_xslt_filter_module-debug.so /usr/lib/nginx/modules/ngx_http_xslt_filter_module-debug.so \
	&& install -m755 objs/ngx_http_image_filter_module-debug.so /usr/lib/nginx/modules/ngx_http_image_filter_module-debug.so \
	&& install -m755 objs/ngx_http_geoip_module-debug.so /usr/lib/nginx/modules/ngx_http_geoip_module-debug.so \
	&& install -m755 objs/ngx_stream_geoip_module-debug.so /usr/lib/nginx/modules/ngx_stream_geoip_module-debug.so \
	&& ln -s ../../usr/lib/nginx/modules /etc/nginx/modules \
	&& strip /usr/sbin/nginx* \
	&& strip /usr/lib/nginx/modules/*.so \
	&& rm -rf /usr/src/nginx-$NGINX_VERSION \
	&& apk add --no-cache --virtual .gettext gettext \
	&& mv /usr/bin/envsubst /tmp/ \
	\
	&& runDeps="$( \
		scanelf --needed --nobanner /usr/sbin/nginx /usr/lib/nginx/modules/*.so /tmp/envsubst \
			| awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
			| sort -u \
			| xargs -r apk info --installed \
			| sort -u \
	)" \
	&& apk add --no-cache --virtual .nginx-rundeps $runDeps \
	&& apk del .build-deps \
	&& apk del .gettext \
	&& mv /tmp/envsubst /usr/local/bin/ \
	&& ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log

RUN apk update && apk add xmlsec xmlsec-dev libc-dev libxml2-dev libffi-dev python2-dev expect \
    python3 python3-dev py3-pip git

ENV CONTAINER_DIR=/container
ENV DJANGO_DIR=/container/service
ENV CERT_DIR=/container/certs
ARG DJANGO_VERSION=1.11.0
ARG HTTP_PORT=80

RUN pip3 install Django==${DJANGO_VERSION} \
    gunicorn \
	mock \
    djangorestframework==3.7.7 \
	django-oauth-toolkit==0.12.0 \
	django-cors-middleware \
	django-sslserver \
	requests \
	requests_oauthlib \
	kafka_python==1.3.5 \
	pycrypto \
	pycryptodomex \
	coreapi \
	drf_yasg

RUN git clone -b develop https://github.com/crs4/djangosaml2.git && cd djangosaml2 && python3 setup.py install

RUN ln -sf /usr/bin/python3 /usr/bin/python
RUN mkdir ${DJANGO_DIR}
RUN mkdir ${CERT_DIR}
RUN echo hgwpwd > /etc/nginx/passw
RUN chown nginx:nginx /etc/nginx/passw && chmod 600 /etc/nginx/passw

ADD resources/nginx.conf /etc/nginx/nginx.conf
ADD resources/docker-entrypoint.sh /custom_entrypoint/
ADD resources/wait-for-it.sh /custom_entrypoint/
ADD resources/nginx_https.template /etc/nginx/conf.d/nginx_https.template
ADD resources/gunicorn_start.sh /usr/local/bin
ADD resources/launch_python_development.sh /usr/local/bin/
ADD resources/launch_python_development.exp /usr/local/bin/

RUN addgroup -S gunicorn && adduser -D -S -s /sbin/nologin -G gunicorn gunicorn

VOLUME "/container/service/"
VOLUME "/container/service/hgw_common/"
VOLUME "/container/web_certs/"
VOLUME "/container/certs/"

ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV PYTHONPATH=$CONTAINER_DIR

RUN chmod +x /custom_entrypoint/docker-entrypoint.sh
RUN chmod +x /custom_entrypoint/wait-for-it.sh

WORKDIR ${DJANGO_DIR}

STOPSIGNAL SIGTERM


