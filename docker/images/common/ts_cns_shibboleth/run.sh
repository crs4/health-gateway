#!/bin/bash
/opt/shibboleth-idp/bin/build.sh

if [[ -z "${DEVELOPMENT}" ]]; then
    envsubst '${SERVER_NAME}' < /etc/apache2/sites-available/shibboleth-virtual-host.prod.conf.template > /etc/apache2/sites-available/shibboleth-virtual-host.prod.conf
    a2ensite shibboleth-virtual-host.prod.conf
else
    envsubst '${SERVER_NAME}' < /etc/apache2/sites-available/shibboleth-virtual-host.dev.conf.template > /etc/apache2/sites-available/shibboleth-virtual-host.dev.conf
    a2ensite shibboleth-virtual-host.dev.conf
fi
apache2ctl start

envsubst '${SERVER_NAME}' < /opt/shibboleth-idp/conf/idp.properties.template > /opt/shibboleth-idp/conf/idp.properties

#JAVA_OPTS="-Djava.awt.headless=true -XX:+UseConcMarkSweepGC -Djava.util.logging.config.file=/var/lib/tomcat8/conf/logging.properties" 
CATALINA_TMPDIR=/tmp/ \
CATALINA_PID="/var/run/tomcat8.pid" \
CATALINA_HOME=/usr/share/tomcat8 \
CATALINA_BASE=/var/lib/tomcat8 \
JSSE_HOME=/usr/lib/jvm/java-8-oracle/jre/ \
/usr/share/tomcat8/bin/catalina.sh run