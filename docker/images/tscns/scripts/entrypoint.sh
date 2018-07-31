#!/bin/bash
if [[ -z ${SERVER_NAME} ]]; then
    echo "Server name not found. Set SERVER_NAME env variable."
    exit 1
fi

if [[ -z ${HGW_FRONTEND_ADDR} ]]; then
    echo "HGW Frontend address not found. Set HGW_FRONTEND_ADDR env variable."
    exit 1
fi

if [[ -z ${CONSENT_MANAGER_ADDR} ]]; then
    echo "Consent Manager address not found. Set CONSENT_MANAGER_ADDR env variable."
    exit 1
fi

SHIBBOLETH_BASE_DIR=/opt/shibboleth-idp
SHIBBOLETH_CREDENTIALS_DIR=${SHIBBOLETH_BASE_DIR}/credentials
SHIBBOLETH_METADATA=${SHIBBOLETH_BASE_DIR}/metadata/idp-metadata.xml

for f in idp-backchannel idp-signing idp-encryption; do
    if [[ ! -f ${SHIBBOLETH_CREDENTIALS_DIR}/${f}.crt ]]; then
        echo "$f.crt not found. You should mount it in $SHIBBOLETH_CREDENTIALS_DIR/$f.crt"
        exit 1
    fi

    if [[ "$f" != "idp-backchannel" ]]; then
        if [[ ! -f ${SHIBBOLETH_CREDENTIALS_DIR}/${f}.key ]]; then
            echo "$f.key not found. You should mount it in $SHIBBOLETH_CREDENTIALS_DIR/$f.key"
            exit 1
        fi
    else
        if [[ ! -f ${SHIBBOLETH_CREDENTIALS_DIR}/${f}.p12 ]]; then
            echo "$f.p12 not found. You should mount it in $SHIBBOLETH_CREDENTIALS_DIR/$f.p12"
            exit 1
        fi
    fi
done

/container/replace_certs.sh

envsubst '${HGW_FRONTEND_ADDR} ${CONSENT_MANAGER_ADDR}' < /opt/shibboleth-idp/conf/metadata-providers.xml.template > /opt/shibboleth-idp/conf/metadata-providers.xml

if [[ -z ${DEVELOPMENT} ]]; then
    if [[ -z ${SSL} ]]; then
        envsubst '${SERVER_NAME}' < /etc/apache2/sites-available/shibboleth-virtual-host.prod.conf.template > /etc/apache2/sites-available/shibboleth-virtual-host.prod.conf
    else
        envsubst '${SERVER_NAME}' < /etc/apache2/sites-available/shibboleth-virtual-host.prod-ssl.conf.template > /etc/apache2/sites-available/shibboleth-virtual-host.prod.conf
    fi
    a2ensite shibboleth-virtual-host.prod.conf
else
    if [[ -z ${SSL} ]]; then
        envsubst '${SERVER_NAME}' < /etc/apache2/sites-available/shibboleth-virtual-host.dev.conf.template > /etc/apache2/sites-available/shibboleth-virtual-host.dev.conf
    else
        envsubst '${SERVER_NAME}' < /etc/apache2/sites-available/shibboleth-virtual-host.dev-ssl.conf.template > /etc/apache2/sites-available/shibboleth-virtual-host.prod.conf
    fi
    a2ensite shibboleth-virtual-host.dev.conf
fi
apache2ctl start

envsubst '${SERVER_NAME}' < /opt/shibboleth-idp/conf/idp.properties.template > /opt/shibboleth-idp/conf/idp.properties

/opt/shibboleth-idp/bin/build.sh

#JAVA_OPTS="-Djava.awt.headless=true -XX:+UseConcMarkSweepGC -Djava.util.logging.config.file=/var/lib/tomcat8/conf/logging.properties" 
CATALINA_TMPDIR=/tmp/ \
CATALINA_PID="/var/run/tomcat8.pid" \
CATALINA_HOME=/usr/share/tomcat8 \
CATALINA_BASE=/var/lib/tomcat8 \
JSSE_HOME=/usr/lib/jvm/java-8-oracle/jre/ \
/usr/share/tomcat8/bin/catalina.sh run