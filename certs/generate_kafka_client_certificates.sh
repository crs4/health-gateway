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


CLIENT_NAME=$1
PASSKEY=hgwpwd
KAFKA_CA_CERT=ca/kafka/certs/ca/kafka.cert.pem
KAFKA_CA_KEY=ca/kafka/certs/ca/kafka.key.pem
ROOT_CA_CERT=ca/root/ca.cert.pem

CLIENT_BASE_DIR=ca/kafka/certs/${CLIENT_NAME}
mkdir -p ${CLIENT_BASE_DIR}
CLIENT_KEYSTORE=${CLIENT_BASE_DIR}/keystore.jks
CLIENT_TRUSTSTORE=${CLIENT_BASE_DIR}/truststore.jks
CLIENT_CERT=${CLIENT_BASE_DIR}/cert.pem
CLIENT_KEY=${CLIENT_BASE_DIR}/key.pem

if [ -z "${CLIENT_NAME}" ]; then
	echo "You should specify the client name"
	exit 1
fi

echo "Creating the client key and certificate"
keytool -keystore ${CLIENT_KEYSTORE} -storepass ${PASSKEY} -keypass ${PASSKEY} -alias ${CLIENT_NAME} \
    -validity 365 -genkey -keyalg RSA -ext SAN=DNS:${CLIENT_NAME} \
    -dname "CN=${CLIENT_NAME},ST=Italy,C=IT"

echo "Adding the CA certificate to the client trustore"
keytool -keystore ${CLIENT_TRUSTSTORE} -noprompt -storepass ${PASSKEY} -alias rootca -import -file ${ROOT_CA_CERT}
keytool -keystore ${CLIENT_TRUSTSTORE} -noprompt -storepass ${PASSKEY} -alias kafkaca -import -file ${KAFKA_CA_CERT}

echo "Extracting the client certificate from the keystore"
keytool -keystore ${CLIENT_KEYSTORE} -storepass ${PASSKEY} -alias ${CLIENT_NAME} -certreq -file ${CLIENT_CERT}

echo "Signing the client certificate with the CA key"
openssl x509 -req -CA ${KAFKA_CA_CERT} -CAkey ${KAFKA_CA_KEY} -in ${CLIENT_CERT} -out ${CLIENT_CERT}.signed -days 365 \
    -CAcreateserial -passin pass:${PASSKEY}

echo "Adding CA and client certificates to the client keystore"
keytool -keystore ${CLIENT_KEYSTORE} -noprompt -storepass ${PASSKEY} -alias rootca -import -file ${ROOT_CA_CERT}
keytool -keystore ${CLIENT_KEYSTORE} -noprompt -storepass ${PASSKEY} -alias kafkaca -import -file ${KAFKA_CA_CERT}
keytool -keystore ${CLIENT_KEYSTORE} -noprompt -storepass ${PASSKEY} -alias ${CLIENT_NAME} -import -file ${CLIENT_CERT}.signed

echo "Extracting client key"
keytool -importkeystore -srckeystore ${CLIENT_KEYSTORE} -noprompt -storepass ${PASSKEY} -srcalias ${CLIENT_NAME} \
    -destkeystore cert_and_key.p12 -deststoretype PKCS12

openssl pkcs12 -in cert_and_key.p12 -passin pass:${PASSKEY} -nocerts -nodes > ${CLIENT_KEY}

rm ${CLIENT_CERT} cert_and_key.p12
mv ${CLIENT_CERT}.signed ${CLIENT_CERT}
