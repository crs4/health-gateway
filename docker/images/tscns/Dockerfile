FROM ubuntu:16.04

RUN apt-get update

# Create some env variables
ENV JAVA_HOME=/usr/lib/jvm/java-8-oracle/jre
ENV IDP_SRC=/usr/local/src/shibboleth-identity-provider-3.3.1
ENV ANT_OPTS="-Didp.src.dir=/usr/local/src/shibboleth-identity-provider-3.3.1 \
-Didp.target.dir=/opt/shibboleth-idp -Didp.host.name=changeit \
-Didp.sealer.password=hgwpwd -Didp.sealer.alias=hgw -Didp.keystore.password=hgwpwd \
-Didp.scope=healthgateway.it -Didp.uri.subject.alt.name=https://changeit/idp/shibboleth"

# Install packages
RUN apt-get -y install ca-certificates openssl apache2 ntp wget less net-tools iputils-ping gettext-base

# Install Oracle Java
RUN apt-get update && \
  apt-get install -y --no-install-recommends locales && \
  locale-gen en_US.UTF-8 && \
  apt-get dist-upgrade -y && \
  apt-get --purge -y remove openjdk* && \
  echo "oracle-java8-installer shared/accepted-oracle-license-v1-1 select true" | debconf-set-selections && \
  echo "deb http://ppa.launchpad.net/webupd8team/java/ubuntu xenial main" > /etc/apt/sources.list.d/webupd8team-java-trusty.list && \
  apt-key adv --keyserver keyserver.ubuntu.com --recv-keys EEA14886 && \
  apt-get update && \
  apt-get install -y --no-install-recommends oracle-java8-installer oracle-java8-set-default && \
  apt-get clean all

# Tomcat Installation and Configuration
RUN apt install -y tomcat8
COPY conf/tomcat/tomcat-server.xml /etc/tomcat8/server.xml
COPY conf/tomcat/idp.xml /etc/tomcat8/Catalina/localhost/idp.xml
COPY conf/tomcat/tomcat-context.xml /etc/tomcat8/context.xml
COPY conf/tomcat/tomcat-default /etc/default/tomcat8
WORKDIR /usr/share/tomcat8/lib/

# Apache configuration
COPY conf/apache/idp.conf /etc/apache2/sites-available/idp.conf
COPY conf/apache/shibboleth-virtual-host.dev.conf.template /etc/apache2/sites-available/shibboleth-virtual-host.dev.conf.template
COPY conf/apache/shibboleth-virtual-host.prod.conf.template /etc/apache2/sites-available/shibboleth-virtual-host.prod.conf.template
COPY conf/apache/shibboleth-virtual-host.dev-ssl.conf.template /etc/apache2/sites-available/shibboleth-virtual-host.dev-ssl.conf.template
COPY conf/apache/shibboleth-virtual-host.prod-ssl.conf.template /etc/apache2/sites-available/shibboleth-virtual-host.prod-ssl.conf.template
COPY conf/apache/ports.conf /etc/apache2/ports.conf
RUN a2enmod ssl headers proxy_ajp
RUN a2ensite idp.conf
RUN a2dissite 000-default.conf

# Shibboleth installation
WORKDIR /usr/local/src
RUN wget http://shibboleth.net/downloads/identity-provider/3.3.1/shibboleth-identity-provider-3.3.1.tar.gz
RUN tar -xzvf shibboleth-identity-provider-3.3.1.tar.gz
WORKDIR /usr/local/src/shibboleth-identity-provider-3.3.1
COPY web_gui/x509-prompt.jsp /usr/local/src/shibboleth-identity-provider-3.3.1/webapp/x509-prompt.jsp
COPY web_gui/bootstrap.css /usr/local/src/shibboleth-identity-provider-3.3.1/webapp/css/bootstrap.css
COPY web_gui/bootstrap.min.css /usr/local/src/shibboleth-identity-provider-3.3.1/webapp/css/bootstrap.min.css
COPY web_gui/bootstrap-responsive.css /usr/local/src/shibboleth-identity-provider-3.3.1/webapp/css/bootstrap-responsive.css
COPY web_gui/bootstrap-responsive.min.css /usr/local/src/shibboleth-identity-provider-3.3.1/webapp/css/bootstrap-responsive.min.css
RUN mkdir /opt/shibboleth-idp
RUN ./bin/install.sh
RUN wget https://build.shibboleth.net/nexus/service/local/repositories/thirdparty/content/javax/servlet/jstl/1.2/jstl-1.2.jar -O /opt/shibboleth-idp/edit-webapp/WEB-INF/lib/jstl-1.2.jar
RUN ./bin/build.sh -Didp.target.dir=/opt/shibboleth-idp
RUN chown -R tomcat8 /opt/shibboleth-idp/logs/
RUN chown -R tomcat8 /opt/shibboleth-idp/metadata/
RUN chown -R tomcat8 /opt/shibboleth-idp/credentials/
RUN chown -R tomcat8 /opt/shibboleth-idp/conf
COPY web_gui/attribute-release.vm /opt/shibboleth-idp/views/intercept/attribute-release.vm

WORKDIR /opt/shibboleth-idp
RUN ./bin/build.sh
COPY conf/shibboleth/subject-c14n.xml /opt/shibboleth-idp/conf/c14n/subject-c14n.xml
COPY conf/shibboleth/global.xml /opt/shibboleth-idp/conf/global.xml
COPY conf/shibboleth/attribute-resolver.xml /opt/shibboleth-idp/conf/attribute-resolver.xml
COPY conf/shibboleth/attribute-filter.xml /opt/shibboleth-idp/conf/attribute-filter.xml
COPY conf/shibboleth/metadata-providers.xml.template /opt/shibboleth-idp/conf/metadata-providers.xml.template
COPY conf/shibboleth/idp.properties.template /opt/shibboleth-idp/conf/idp.properties.template
#COPY conf/shibboleth/web.xml /opt/shibboleth-idp/webapp/WEB-INF/web.xml
#Disable this in production - too noise log levels
COPY conf/shibboleth/logback.xml /opt/shibboleth-idp/conf/logback.xml

COPY metadata/idp-metadata.xml.template /opt/shibboleth-idp/metadata/idp-metadata.xml.template

# Copy certificates. TODO: This will be volumes
RUN mkdir /root/certificates
COPY certs/ca-CNS-bundle.crt /root/certificates/

RUN mkdir /container/
COPY scripts/replace_certs.sh /container/
COPY scripts/entrypoint.sh /container/entrypoint.sh
RUN chmod +x /container/replace_certs.sh
RUN chmod +x /container/entrypoint.sh

EXPOSE 443

VOLUME /opt/shibboleth-idp/credentials/
VOLUME /root/certificates/
VOLUME /root/metadata/


ENTRYPOINT ["/container/entrypoint.sh"]
