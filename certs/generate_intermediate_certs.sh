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



INT_NAME=$1

if [ -z "${INT_NAME}" ]; then
	echo "You should specify the intermediate CA name"
	exit 1
fi

export INT_NAME
export ROOT_BASE_DIR=$PWD/ca/root
export INT_BASE_DIR=$PWD/ca/${INT_NAME}

if [ -d "${INT_BASE_DIR}" ]; then
    while true; do
        read -p "The ${INT_NAME} CA already exists? This will erase all existing data. Do you want to continue (y/n)? " YN
        case ${YN} in
            [Yy]* ) break;;
            [Nn]* ) exit;;
            * ) echo "Please answer yes or no.";;
        esac
    done
fi

INT_INDEX_FILE=${INT_BASE_DIR}/index.txt
INT_CONF=${PWD}/intermediate_openssl.cnf

ROOT_CA_CONF=${PWD}/openssl.cnf
ROOT_CA_CERT=${ROOT_BASE_DIR}/ca.cert.pem

KEY_FILE=${INT_BASE_DIR}/certs/ca/${INT_NAME}.key.pem
CSR_FILE=${INT_BASE_DIR}/certs/ca/${INT_NAME}.csr.pem
CERT_FILE=${INT_BASE_DIR}/certs/ca/${INT_NAME}.cert.pem
CHAIN_FILE=${INT_BASE_DIR}/certs/ca/${INT_NAME}.chain.cert.pem
CN_NAME="$(tr '[:lower:]' '[:upper:]' <<< ${INT_NAME:0:1})${INT_NAME:1}"

PASSKEY=hgwpwd

rm -rf ${INT_BASE_DIR}
mkdir -p ${INT_BASE_DIR}/certs/ca ${INT_BASE_DIR}/crl ${INT_BASE_DIR}/csr \
    ${INT_BASE_DIR}/newcerts
touch ${INT_INDEX_FILE} ${INT_INDEX_FILE}.attr
echo 1000 > ${INT_BASE_DIR}/serial

openssl genrsa -aes256 -passout pass:${PASSKEY} -out ${KEY_FILE} 4096
chmod 400 ${KEY_FILE}
if [ ! $? == 0 ]; then
	echo "Error creating key"
	exit 1;
fi

openssl req -config ${INT_CONF} \
	-new \
	-sha256 \
	-passin pass:${PASSKEY} \
	-key ${KEY_FILE} \
	-out ${CSR_FILE} \
	-subj "/C=IT/ST=Italy/L=Cagliari/O=Fake Certification Institution/OU=Fake Certification Authority/CN=Fake Certification Authority ${CN_NAME} CA/"

if [ ! $? == 0 ]; then
	echo "Error creating csr"
	exit 1;
fi

openssl ca -config ${ROOT_CA_CONF} -extensions v3_intermediate_ca -batch\
	-passin pass:${PASSKEY} \
	-days 3650 -notext -md sha256 \
	-in ${CSR_FILE} \
	-out ${CERT_FILE}

if [ ! $? == 0 ]; then
	echo "Error creating cert"
	exit 1;
fi

chmod 444 ${CERT_FILE}
echo "Certs and key created"

echo "Verifying cert against root cert"
openssl verify -CAfile ${ROOT_CA_CERT} ${CERT_FILE}

echo "Creating chain file"
cat ${CERT_FILE} ${ROOT_CA_CERT} > ${CHAIN_FILE}
chmod 444 ${CHAIN_FILE}