FROM mysql:5.7.22
RUN apt-get update
RUN apt-get -y install vim wget less net-tools iputils-ping
RUN sed -i 's/#bind-address\t= 127.0.0.1/bind-address = 0.0.0.0/g' /etc/mysql/mysql.conf.d/mysqld.cnf
COPY shibboleth-db.sql /docker-entrypoint-initdb.d/

