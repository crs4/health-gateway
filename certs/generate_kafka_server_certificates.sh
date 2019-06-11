#!/usr/bin/env bash

# Copyright (c) 2017-2018 CRS4
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
# AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.



KAFKA_CA_CERT=ca/kafka/certs/ca/kafka.cert.pem
KAFKA_CA_KEY=ca/kafka/certs/ca/kafka.key.pem
ROOT_CA_CERT=ca/root/ca.cert.pem
PASSKEY=hgwpwd
SERVER_BASE_DIR=ca/kafka/certs/kafka-server
mkdir -p ${SERVER_BASE_DIR}
SERVER_KEYSTORE=${SERVER_BASE_DIR}/keystore.jks
SERVER_TRUSTSTORE=${SERVER_BASE_DIR}/truststore.jks
SERVER_CERT=${SERVER_BASE_DIR}/cert.pem
SERVER_KEY=${SERVER_BASE_DIR}/key.pem

# Create server keystore and the server certificate
echo "Creating server keystore with cert"
keytool -keystore ${SERVER_KEYSTORE} -storepass ${PASSKEY} -keypass ${PASSKEY} -alias kafkaserver \
    -validity 365 -genkey -keyalg RSA -ext SAN=DNS:kafka \
    -dname "CN=kafka,ST=Italy,C=IT"

# Create server truststore and add the CA cert
# echo "Creating server keystore and adding CA cert"
# keytool -keystore ${SERVER_TRUSTSTORE} -noprompt -storepass ${PASSKEY} -alias kafkaca -import -file ${KAFKA_CA_CERT}
# keytool -keystore ${SERVER_TRUSTSTORE} -noprompt -storepass ${PASSKEY} -alias rootca -import -file ${ROOT_CA_CERT}

# Extract the server certificate
echo "Extract server cert"
keytool -keystore ${SERVER_KEYSTORE} -storepass ${PASSKEY} -alias kafkaserver -certreq -file ${SERVER_CERT}

# Sign the server certificate with the CA key
echo "Signing server certificates with CA key"
openssl x509 -req -CA ${KAFKA_CA_CERT} -CAkey ${KAFKA_CA_KEY} -in ${SERVER_CERT} -out ${SERVER_CERT}.signed -days 365 \
    -CAcreateserial -passin pass:${PASSKEY}

# Add the CA cert and the signed server cert to the the keystore
echo "Adding CA cert and signed server cert to server keystore"
keytool -keystore ${SERVER_KEYSTORE} -noprompt -storepass ${PASSKEY} -alias kafkaca -import -file ${KAFKA_CA_CERT}
keytool -keystore ${SERVER_KEYSTORE} -noprompt -storepass ${PASSKEY} -alias rootca -import -file ${ROOT_CA_CERT}
keytool -keystore ${SERVER_KEYSTORE} -noprompt -storepass ${PASSKEY} -alias kafkaserver -import -file ${SERVER_CERT}.signed

rm ca/kafka/kafka.srl