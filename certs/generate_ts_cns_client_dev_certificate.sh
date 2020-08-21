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


PASSKEY=hgwpwd
WEB_CA_CERT=ca/web/certs/ca/web.cert.pem
WEB_CA_KEY=ca/web/certs/ca/web.key.pem
ROOT_CA_CERT=ca/root/ca.cert.pem

declare -A PERSONS

function create_cert() {
    CLIENT_NAME=$1
    NAME=$2
    SURNAME=$3
    ID=$4

    CLIENT_BASE_DIR=ca/web/certs/${CLIENT_NAME}
    mkdir -p ${CLIENT_BASE_DIR}
    CLIENT_KEYSTORE=${CLIENT_BASE_DIR}/keystore.jks
    CLIENT_TRUSTSTORE=${CLIENT_BASE_DIR}/truststore.jks
    CLIENT_CERT=${CLIENT_BASE_DIR}/cert.pem
    CLIENT_KEY=${CLIENT_BASE_DIR}/key.pem
    CLIENT_CSR=${CLIENT_BASE_DIR}/csr.pem
    CLIENT_P12=${CLIENT_BASE_DIR}/cert.p12

    echo "/C=IT/GN=${NAME}/SN=${SURNAME}/CN=${ID}//0000000000000000.oXPnbQvnvQANlkxAg"
    openssl genrsa -des3 -out ${CLIENT_KEY} 4096
    openssl req -new -key ${CLIENT_KEY} -out ${CLIENT_CSR} \
        -subj /C=IT/CN="\"${ID}\/0000000000000000.oXPnbQvnvQANlkxAg\""/GN=${NAME}/SN=${SURNAME}

    echo "Signing the client certificate with the CA key"

    openssl x509 -req -CA ${WEB_CA_CERT} -CAkey ${WEB_CA_KEY} -in ${CLIENT_CSR} -out ${CLIENT_CERT} -days 365 \
        -CAcreateserial -passin pass:${PASSKEY}
    openssl pkcs12 -export -out ${CLIENT_P12} -inkey ${CLIENT_KEY} -in ${CLIENT_CERT} -CAfile ${WEB_CA_KEY}

}
#create_cert "garibaldi" "Giuseppe" "Garibaldi" "GRBGPP87L04L741X"
#create_cert "cesare" "Giulio" "Cesare" "CSRGGL44L13H501E"
#create_cert "darco" "Giovanna" "D'Arco" "DRCGNN12A46A326K"

create_cert $1 $2 $3 $4

