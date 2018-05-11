FROM osixia/openldap:1.1.8
ENV LDAP_ORGANIZATION="Fakespid"
ENV LDAP_DOMAIN="healthgateway.it"
ENV LDAP_ADMIN_PASSWORD="hgwpwd"
ENV LDAP_TLS=false
RUN apt-get update
RUN apt-get -y install vim wget less net-tools iputils-ping
ADD resources/mickeymouse.ldif /
ADD resources/donaldduck.ldif /
ADD resources/italianperson.schema  /container/service/slapd/assets/config/bootstrap/schema/mmc/italianperson.schema
ADD resources/startup.sh /container/service/slapd/startup.sh
RUN chmod +x /container/service/slapd/startup.sh