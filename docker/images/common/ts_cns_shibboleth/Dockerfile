FROM ubuntu:16.04

RUN apt-get update

# Create some env variables
ENV JAVA_HOME=/usr/lib/jvm/java-8-oracle/jre
ENV IDP_SRC=/usr/local/src/shibboleth-identity-provider-3.3.1
ENV ANT_OPTS="-Didp.src.dir=/usr/local/src/shibboleth-identity-provider-3.3.1 \
-Didp.target.dir=/opt/shibboleth-idp -Didp.host.name=fakespid.healthgateway.it \
-Didp.sealer.password=hgwdev -Didp.sealer.alias=hgwdev -Didp.keystore.password=hgwdev \
-Didp.scope=healthgateway.it -Didp.uri.subject.alt.name=https://fakespid.healthgateway.it/idp/shibboleth"

# Install packages
RUN apt-get -y install ca-certificates openssl apache2 ntp wget less net-tools iputils-ping \
libmysql-java libcommons-dbcp-java libcommons-pool-java

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
RUN ln -s ../../java/mysql.jar mysql-connector-java.jar
RUN ln -s ../../java/tomcat-jbcp.jar tomcat-jbcp.jar

# Apache configuration
COPY conf/apache/idp.conf /etc/apache2/sites-available/idp.conf
COPY conf/apache/shibboleth-virtual-host.prod.conf /etc/apache2/sites-available/shibboleth-virtual-host.prod.conf
COPY conf/apache/shibboleth-virtual-host.dev.conf /etc/apache2/sites-available/shibboleth-virtual-host.dev.conf
COPY conf/apache/ports.conf /etc/apache2/ports.conf
RUN a2enmod ssl headers proxy_ajp
RUN a2ensite idp.conf
RUN a2dissite 000-default.conf

# Shibboleth installation
WORKDIR /usr/local/src
RUN wget http://shibboleth.net/downloads/identity-provider/3.3.1/shibboleth-identity-provider-3.3.1.tar.gz
RUN tar -xzvf shibboleth-identity-provider-3.3.1.tar.gz
WORKDIR /usr/local/src/shibboleth-identity-provider-3.3.1
RUN mkdir /opt/shibboleth-idp
RUN ./bin/install.sh
RUN wget https://build.shibboleth.net/nexus/service/local/repositories/thirdparty/content/javax/servlet/jstl/1.2/jstl-1.2.jar -O /opt/shibboleth-idp/edit-webapp/WEB-INF/lib/jstl-1.2.jar
RUN ./bin/build.sh -Didp.target.dir=/opt/shibboleth-idp
RUN chown -R tomcat8 /opt/shibboleth-idp/logs/
RUN chown -R tomcat8 /opt/shibboleth-idp/metadata/
RUN chown -R tomcat8 /opt/shibboleth-idp/credentials/
RUN chown -R tomcat8 /opt/shibboleth-idp/conf

WORKDIR /opt/shibboleth-idp
RUN ./bin/build.sh
COPY conf/shibboleth/saml-nameid.xml /opt/shibboleth-idp/conf/saml-nameid.xml
COPY conf/shibboleth/saml-nameid.properties /opt/shibboleth-idp/conf/saml-nameid.properties
COPY conf/shibboleth/subject-c14n.xml /opt/shibboleth-idp/conf/c14n/subject-c14n.xml
COPY conf/shibboleth/global.xml /opt/shibboleth-idp/conf/global.xml
COPY conf/shibboleth/attribute-resolver.xml /opt/shibboleth-idp/conf/attribute-resolver.xml
COPY conf/shibboleth/attribute-filter.xml /opt/shibboleth-idp/conf/attribute-filter.xml
COPY conf/shibboleth/metadata-providers.xml /opt/shibboleth-idp/conf/metadata-providers.xml
COPY conf/shibboleth/idp.properties /opt/shibboleth-idp/conf/idp.properties
#Disable this in production - too noise log levels
#COPY logback.xml /opt/shibboleth-idp/conf/logback.xml

COPY metadata/idp-metadata.xml /opt/shibboleth-idp/metadata/idp-metadata.xml
COPY metadata/sp-metadata-hgw-frontend.xml /opt/shibboleth-idp/metadata/sp-metadata-hgw-frontend.xml
COPY metadata/sp-metadata-consent-manager.xml /opt/shibboleth-idp/metadata/sp-metadata-consent-manager.xml
COPY credentials/* /opt/shibboleth-idp/credentials/


# Copy certificates. TODO: This will be volumes
RUN mkdir /root/certificates
COPY certs/idp-cert-server.crt /root/certificates/
COPY certs/idp-key-server.key /root/certificates/
COPY certs/ca-CNS-bundle.crt /root/certificates
COPY certs/ca-development.crt /root/certificates
RUN chmod 400 /root/certificates/idp-key-server.key
RUN chmod 644 /root/certificates/idp-cert-server.crt

#install module for X.509 CLIENT CERTIFICATE SLL auth

#WORKDIR /usr/local
#RUN apt-get -y install maven
#RUN apt-get -y install subversion
#RUN svn export https://subversion.switch.ch/svn/general/aai/java-idp-x509-login-handler/trunk/ java-idp-x509-login-handler
#WORKDIR /usr/local/java-idp-x509-login-handler
#RUN mvn package
#RUN wget https://forge.switch.ch/attachments/download/674/x509-login-handler-0.5.0.jar
#RUN cp x509-login-handler-0.5.0.jar /opt/shibboleth-idp/lib
#COPY X509-login.jsp /opt/shibboleth-idp/src/main/webapp/

COPY run.sh /usr/local/bin/run.sh 
RUN chmod +x /usr/local/bin/run.sh 

EXPOSE 443

ENTRYPOINT ["run.sh"]
