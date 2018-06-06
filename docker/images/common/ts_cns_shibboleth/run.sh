#!/bin/bash
if [[ -z "${DEVELOPMENT}" ]]; then
    a2ensite shibboleth-virtual-host.prod.conf
else
    a2ensite shibboleth-virtual-host.dev.conf
fi
apache2ctl start

#JAVA_OPTS="-Djava.awt.headless=true -XX:+UseConcMarkSweepGC -Djava.util.logging.config.file=/var/lib/tomcat8/conf/logging.properties" 
CATALINA_TMPDIR=/tmp/ \
CATALINA_PID="/var/run/tomcat8.pid" \
CATALINA_HOME=/usr/share/tomcat8 \
CATALINA_BASE=/var/lib/tomcat8 \
JSSE_HOME=/usr/lib/jvm/java-8-openjdk-amd64/jre/ \
/usr/share/tomcat8/bin/catalina.sh run