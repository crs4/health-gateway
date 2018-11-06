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

INT_NAME=web
SERVICE_NAME=$1
OUTPUT_NAME=$2
NO_PASSW=$3

if [ -z "${SERVICE_NAME}" ]; then
	echo "You should specify the service name"
	exit 1
fi

PASSKEY=hgwpwd

export INT_NAME
export ROOT_BASE_DIR=$PWD/ca/root
export INT_BASE_DIR=$PWD/ca/${INT_NAME}
INT_CONF=${PWD}/intermediate_openssl.cnf
INT_CERT=${INT_BASE_DIR}/certs/ca/${INT_NAME}.cert.pem
INT_CHAIN_CERT=${INT_BASE_DIR}/certs/ca/${INT_NAME}.chain.cert.pem

CERTS_DIR=${INT_BASE_DIR}/certs/${SERVICE_NAME}
mkdir -p ${CERTS_DIR}
CSR_FILE=${INT_BASE_DIR}/csr/${SERVICE_NAME}.csr.pem

if [ -z "${OUTPUT_NAME}" ]; then
    KEY_FILE=${CERTS_DIR}/key.pem
    CERT_FILE=${CERTS_DIR}/cert.pem
else
    KEY_FILE=${OUTPUT_NAME}.key.pem
    CERT_FILE=${OUTPUT_NAME}.cert.pem
fi

rm -f ${KEY_FILE} ${CSR_FILE} ${CERT_FILE}

openssl genrsa -aes256 -passout pass:${PASSKEY} -out ${KEY_FILE} 2048
chmod 400 ${KEY_FILE}

echo "Creating request"
openssl req -config ${INT_CONF} \
	-new \
	-sha256 \
	-passin pass:${PASSKEY} \
	-key ${KEY_FILE} \
	-out ${CSR_FILE} \
	-subj "/C=IT/ST=Italy/CN=${SERVICE_NAME}/"

echo "Signing"
openssl ca -config ${INT_CONF} -extensions server_cert -batch \
	-passin pass:${PASSKEY} \
	-days 365 -notext -md sha256 \
	-in ${CSR_FILE} \
	-out ${CERT_FILE}
chmod 444 ${CERT_FILE}

if [ "$NO_PASSW" == "true" ]; then
    openssl rsa -in ${KEY_FILE} -out ${KEY_FILE}.tmp -passin pass:${PASSKEY}
    mv -f ${KEY_FILE}.tmp ${KEY_FILE}
fi

echo "Verifying chain of trust"
openssl verify -CAfile ${INT_CHAIN_CERT} ${CERT_FILE}