FROM ubuntu:16.04

RUN apt-get update
RUN apt-get -y install vim default-jdk ca-certificates openssl tomcat8 apache2 ntp wget less net-tools iputils-ping \
libmysql-java libmysql-java libcommons-dbcp-java libcommons-pool-java
ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64/jre
ENV IDP_SRC=/usr/local/src/shibboleth-identity-provider-3.3.1
ENV ANT_OPTS="-Didp.src.dir=/usr/local/src/shibboleth-identity-provider-3.3.1 \
-Didp.target.dir=/opt/shibboleth-idp -Didp.host.name=fakespid.healthgateway.it \
-Didp.sealer.password=hgwdev -Didp.sealer.alias=hgwdev -Didp.keystore.password=hgwdev \
-Didp.scope=healthgateway.it -Didp.uri.subject.alt.name=https://fakespid.healthgateway.it/idp/shibboleth"
RUN mkdir /root/certificates
COPY idp-cert-server.crt /root/certificates
COPY idp-key-server.key /root/certificates
RUN chmod 400 /root/certificates/idp-key-server.key
RUN chmod 644 /root/certificates/idp-cert-server.crt
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
COPY shibboleth-virtual-host.conf /etc/apache2/sites-available/shibboleth-virtual-host.conf
COPY ports.conf /etc/apache2/ports.conf
COPY tomcat-server.xml /etc/tomcat8/server.xml
COPY idp.xml /etc/tomcat8/Catalina/localhost/idp.xml
COPY idp.conf /etc/apache2/sites-available/idp.conf
COPY tomcat-context.xml /etc/tomcat8/context.xml
COPY tomcat-default /etc/default/tomcat8
COPY idp.properties /opt/shibboleth-idp/conf/idp.properties
RUN a2enmod ssl headers proxy_ajp
RUN a2ensite shibboleth-virtual-host.conf idp.conf
RUN a2dissite 000-default.conf
COPY run.sh /usr/local/bin/run.sh 
RUN chmod +x /usr/local/bin/run.sh 

RUN apt-get -y install

WORKDIR /usr/share/tomcat8/lib/
RUN ln -s ../../java/mysql.jar mysql-connector-java.jar
RUN ln -s ../../java/tomcat-jbcp.jar tomcat-jbcp.jar

WORKDIR /opt/shibboleth-idp
RUN ./bin/build.sh
COPY saml-nameid.properties /opt/shibboleth-idp/conf/saml-nameid.properties
COPY saml-nameid.xml /opt/shibboleth-idp/conf/saml-nameid.xml
COPY subject-c14n.xml /opt/shibboleth-idp/conf/c14n/subject-c14n.xml
COPY global.xml /opt/shibboleth-idp/conf/global.xml
COPY ldap.properties /opt/shibboleth-idp/conf/ldap.properties
COPY attribute-resolver.xml /opt/shibboleth-idp/conf/attribute-resolver.xml
COPY attribute-filter.xml /opt/shibboleth-idp/conf/attribute-filter.xml
COPY metadata-providers.xml /opt/shibboleth-idp/conf/metadata-providers.xml
COPY idp-metadata.xml /opt/shibboleth-idp/metadata/idp-metadata.xml
COPY sp-metadata-hgw-frontend.xml /opt/shibboleth-idp/metadata/sp-metadata-hgw-frontend.xml
COPY sp-metadata-consent-manager.xml /opt/shibboleth-idp/metadata/sp-metadata-consent-manager.xml
COPY credentials/* /opt/shibboleth-idp/credentials/

EXPOSE 443

ENTRYPOINT ["run.sh"]
